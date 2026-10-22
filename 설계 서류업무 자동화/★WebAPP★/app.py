# -*- coding: utf-8 -*-
"""
설계 서류업무 자동화 허브 - Flask 웹 버전
여러 개의 독립된 tkinter+xlwings/openpyxl 자동화 스크립트를 하나의 웹 허브로 통합.
xlwings(실제 Excel 프로그램 제어)로 하던 이미지 삽입 / 시트 서식 복사는
openpyxl만으로 동일하게 재현해서, 서버에 Excel 설치 없이도 여러 명이 동시에 쓸 수 있게 했다.
"""
import io
import os
import re
import tempfile
import uuid
from copy import copy as copy_style

from flask import Flask, render_template, request, send_file, jsonify
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from PIL import Image as PILImage

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300MB (사진/PDF 다건 업로드 고려)

ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}


# ====================================================================
# 공용 helper - openpyxl로 xlwings와 동일한 효과 재현
# ====================================================================
def place_image(ws, img_path, base_cell, width_px, height_px, dx_px=0, dy_px=0):
    """base_cell 좌상단에서 (dx_px, dy_px) 픽셀만큼 떨어진 위치에 이미지를 절대 배치.
    xlwings의 `pictures.add(left=cell.left+dx, top=cell.top, width=.., height=..)`와 동일한 효과."""
    row, col = _cell_to_rowcol(base_cell)
    marker = AnchorMarker(col=col - 1, colOff=pixels_to_EMU(dx_px), row=row - 1, rowOff=pixels_to_EMU(dy_px))
    size = XDRPositiveSize2D(cx=pixels_to_EMU(width_px), cy=pixels_to_EMU(height_px))

    img = XLImage(img_path)
    if str(getattr(img, "format", "")).lower() not in ("png", "jpeg", "gif"):
        img.format = "png"
    img.anchor = OneCellAnchor(_from=marker, ext=size)
    ws.add_image(img)


def _cell_to_rowcol(cell_ref):
    from openpyxl.utils.cell import coordinate_to_tuple
    row, col = coordinate_to_tuple(cell_ref)
    return row, col


def copy_sheet_contents(src_ws, dst_ws):
    """다른 워크북의 시트를 값+서식+병합+열너비/행높이까지 복사 (xlwings의
    `Cells.Copy` + `PasteSpecial(xlPasteAll)`을 openpyxl로 재현)."""
    dst_ws.delete_rows(1, dst_ws.max_row or 1)

    for row in src_ws.iter_rows():
        for cell in row:
            new_cell = dst_ws.cell(row=cell.row, column=cell.column, value=cell.value)
            if cell.has_style:
                new_cell.font = copy_style(cell.font)
                new_cell.border = copy_style(cell.border)
                new_cell.fill = copy_style(cell.fill)
                new_cell.number_format = cell.number_format
                new_cell.protection = copy_style(cell.protection)
                new_cell.alignment = copy_style(cell.alignment)

    for merged_range in src_ws.merged_cells.ranges:
        try:
            dst_ws.merge_cells(str(merged_range))
        except Exception:
            pass

    for col_letter, dim in src_ws.column_dimensions.items():
        if dim.width:
            dst_ws.column_dimensions[col_letter].width = dim.width
    for row_idx, dim in src_ws.row_dimensions.items():
        if dim.height:
            dst_ws.row_dimensions[row_idx].height = dim.height


def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, "_", filename)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def save_upload(file_storage, tmp_dir):
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1]
    fd, path = tempfile.mkstemp(suffix=ext, dir=tmp_dir)
    os.close(fd)
    file_storage.save(path)
    return path


def save_uploads_sorted(file_list, tmp_dir):
    """여러 파일을 업로드된 원래 파일명 기준으로 정렬해서 저장 (원본 스크립트의
    `sorted(os.listdir(folder))` 폴더-선택 방식과 동일한 순서 보장)."""
    items = [(f.filename, f) for f in file_list if f and f.filename]
    items.sort(key=lambda x: x[0])
    paths = []
    for filename, f in items:
        ext = os.path.splitext(filename)[1]
        fd, path = tempfile.mkstemp(suffix=ext, dir=tmp_dir)
        os.close(fd)
        f.save(path)
        paths.append((filename, path))
    return paths


def is_allowed_image(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXT


def send_workbook(wb, download_name, warnings=None):
    wb.calculation.calcMode = "manual"
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    buf.seek(0)
    response = send_file(
        buf,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    if warnings:
        import base64
        encoded = base64.b64encode("\n".join(warnings).encode("utf-8")).decode("ascii")
        response.headers["X-Warnings-B64"] = encoded
    response.headers["Access-Control-Expose-Headers"] = "X-Warnings-B64"
    return response


# ====================================================================
# 허브 랜딩 페이지
# ====================================================================
TOOLS = [
    {
        "id": "mobis-siunjeon",
        "name": "MOBIS 시운전완료보고자료 자동화",
        "desc": "금형 사진 3장 + 제품사진 + 자재표를 업로드하면 시운전완료보고자료 엑셀을 자동 생성합니다.",
        "status": "ready",
    },
    {
        "id": "mobis-injatable",
        "name": "MOBIS 인자표 자동화",
        "desc": "전극사진 여러 장, 금형사진 여러 장, 제품사진을 인자표 엑셀에 자동으로 삽입합니다.",
        "status": "ready",
    },
    {
        "id": "sl-qcs",
        "name": "SL 웹서버 QCS 승인원 자동화",
        "desc": "금형 명판/핫런너/열린/닫힌 사진과 전극사진, 금형자재표를 승인원 엑셀에 자동 반영합니다.",
        "status": "ready",
    },
    {
        "id": "sl-approval-full",
        "name": "SL 엑셀파일 승인원 자동화",
        "desc": "금형/전극/습합/충진밸런스 사진, 3D스캐너 PDF, 사출조건표/금형자재표까지 반영하는 전체 승인원 자동화.",
        "status": "ready",
    },
    {
        "id": "sl-factor-template",
        "name": "SL 팩터검증템플릿 제목수정자동화 v3.0",
        "desc": "PPTX 슬라이드 제목의 MP번호·품명을 일괄 치환합니다.",
        "status": "ready",
    },
]


@app.route("/")
def hub():
    return render_template("hub.html", tools=TOOLS)


# ====================================================================
# 1) MOBIS 시운전완료보고자료 자동화
# ====================================================================
SIUNJEON_PHOTO_POSITIONS = {"mold_1": "M5", "mold_2": "B6", "mold_3": "B22", "product": "L23"}
SIUNJEON_IMAGE_SIZES = {
    "mold_1": (350, 240),
    "mold_2": (500, 300),
    "mold_3": (500, 300),
    "product": (500, 300),
}


def siunjeon_insert_images(ws, images, warnings):
    success_count = 0
    for key, path in images.items():
        if not path or not os.path.exists(path):
            continue
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext not in ALLOWED_IMAGE_EXT:
                warnings.append(f"{key}: 지원하지 않는 이미지 형식({ext})이라 삽입하지 않았습니다.")
                continue
            if os.path.getsize(path) == 0:
                warnings.append(f"{key}: 이미지 파일이 비어있습니다.")
                continue
            w, h = SIUNJEON_IMAGE_SIZES.get(key, (300, 200))
            place_image(ws, path, SIUNJEON_PHOTO_POSITIONS[key], w, h)
            success_count += 1
        except Exception as e:
            warnings.append(f"{key}: 이미지 삽입 실패 ({type(e).__name__}: {e})")
    return success_count


def siunjeon_extract_after(text, keyword):
    if not text:
        return ""
    match = re.search(re.escape(keyword) + r"\s*(.*)", text)
    return match.group(1).strip() if match else ""


def siunjeon_apply_material(ws, mat_path, warnings):
    if not mat_path or not os.path.exists(mat_path):
        return None
    try:
        wb_mat = load_workbook(mat_path, data_only=True)
        ws_mat = wb_mat.active

        def safe_get(cell_ref):
            try:
                return ws_mat[cell_ref].value
            except Exception:
                return None

        model = siunjeon_extract_after(safe_get("B2"), "*MODEL :")
        mold = siunjeon_extract_after(safe_get("F2"), "*금형명 :")
        size = siunjeon_extract_after(safe_get("B4"), "*금형 SIZE :")
        weight = siunjeon_extract_after(safe_get("F4"), "*금형 중량 :") or siunjeon_extract_after(safe_get("B2"), "*금형 중량 :")
        wb_mat.close()

        full_name = f"{model} {mold}".strip() or "제품명없음"

        try:
            ws["E3"] = f"제품명 : {full_name}"
        except Exception as e:
            warnings.append(f"E3 셀 업데이트 실패: {e}")
        try:
            if size:
                ws["O15"] = size
        except Exception as e:
            warnings.append(f"O15 셀 업데이트 실패: {e}")
        try:
            if weight:
                ws["O17"] = weight
        except Exception as e:
            warnings.append(f"O17 셀 업데이트 실패: {e}")

        safe_sheet_name = sanitize_filename(full_name[:31])
        safe_sheet_name = re.sub(r"[\[\]\*\?:/\\]", "_", safe_sheet_name)
        try:
            ws.title = safe_sheet_name or "Sheet1"
        except Exception:
            ws.title = "Sheet1"

        return full_name
    except Exception as e:
        warnings.append(f"자재표 처리 실패: {type(e).__name__} - {e}")
        return None


@app.route("/mobis-siunjeon")
def page_mobis_siunjeon():
    return render_template("mobis_siunjeon.html")


@app.route("/mobis-siunjeon/generate", methods=["POST"])
def api_mobis_siunjeon_generate():
    mold_type = request.form.get("mold_type", "일반")
    excel_file = request.files.get("excel_file")

    if not excel_file or not excel_file.filename:
        return jsonify({"error": "시운전보고자료 엑셀 파일을 업로드해주세요."}), 400
    if not excel_file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "엑셀 파일(.xlsx)만 업로드할 수 있습니다."}), 400

    warnings = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = save_upload(excel_file, tmp_dir)
        try:
            wb = load_workbook(excel_path, keep_vba=False, data_only=False)
        except Exception as e:
            return jsonify({"error": f"엑셀 파일을 열 수 없습니다: {type(e).__name__} - {e}"}), 400

        if mold_type == "일반":
            ws = wb.active
            imgs = {
                "mold_1": save_upload(request.files.get("mold_1"), tmp_dir),
                "mold_2": save_upload(request.files.get("mold_2"), tmp_dir),
                "mold_3": save_upload(request.files.get("mold_3"), tmp_dir),
                "product": save_upload(request.files.get("product"), tmp_dir),
            }
            material_path = save_upload(request.files.get("material"), tmp_dir)
            siunjeon_insert_images(ws, imgs, warnings)
            name = siunjeon_apply_material(ws, material_path, warnings) if material_path else "시트"
            if len(wb.sheetnames) > 1:
                wb.remove(wb[wb.sheetnames[1]])
        else:
            ws1 = wb.worksheets[0]
            ws2 = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.create_sheet("2차")
            product_path = save_upload(request.files.get("product"), tmp_dir)
            imgs1 = {
                "mold_1": save_upload(request.files.get("mold_1_1"), tmp_dir),
                "mold_2": save_upload(request.files.get("mold_1_2"), tmp_dir),
                "mold_3": save_upload(request.files.get("mold_1_3"), tmp_dir),
                "product": product_path,
            }
            imgs2 = {
                "mold_1": save_upload(request.files.get("mold_2_1"), tmp_dir),
                "mold_2": save_upload(request.files.get("mold_2_2"), tmp_dir),
                "mold_3": save_upload(request.files.get("mold_2_3"), tmp_dir),
                "product": product_path,
            }
            material1_path = save_upload(request.files.get("material_1"), tmp_dir)
            material2_path = save_upload(request.files.get("material_2"), tmp_dir)
            siunjeon_insert_images(ws1, imgs1, warnings)
            siunjeon_insert_images(ws2, imgs2, warnings)
            name = siunjeon_apply_material(ws1, material1_path, warnings) if material1_path else "시트1"
            siunjeon_apply_material(ws2, material2_path, warnings)

        safe_name = sanitize_filename(name) if name else "시운전보고자료"
        download_name = f"{safe_name}_설치시운전완료보고자료_MK-TECH.xlsx"
        try:
            return send_workbook(wb, download_name, warnings)
        except Exception as e:
            return jsonify({"error": f"엑셀 저장에 실패했습니다: {type(e).__name__} - {e}"}), 500


# ====================================================================
# 2) MOBIS 인자표 자동화
# ====================================================================
INJATABLE_ELECTRODE_SIZE = (80, 80)
INJATABLE_MOLD_SIZE = (90, 90)
INJATABLE_PRODUCT_SIZE = (110, 110)


@app.route("/mobis-injatable")
def page_mobis_injatable():
    return render_template("mobis_injatable.html")


@app.route("/mobis-injatable/generate", methods=["POST"])
def api_mobis_injatable_generate():
    excel_file = request.files.get("excel_file")
    if not excel_file or not excel_file.filename:
        return jsonify({"error": "인자표 엑셀 파일을 업로드해주세요."}), 400
    if not excel_file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "엑셀 파일(.xlsx)만 업로드할 수 있습니다."}), 400

    warnings = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = save_upload(excel_file, tmp_dir)
        try:
            wb = load_workbook(excel_path)
        except Exception as e:
            return jsonify({"error": f"엑셀 파일을 열 수 없습니다: {type(e).__name__} - {e}"}), 400
        ws = wb.worksheets[0]

        electrode_files = request.files.getlist("electrode_images")
        mold_files = request.files.getlist("mold_images")
        product_file = request.files.get("product_image")

        electrode_paths = save_uploads_sorted(electrode_files, tmp_dir)
        mold_paths = save_uploads_sorted(mold_files, tmp_dir)

        for idx, (filename, path) in enumerate(electrode_paths):
            if not is_allowed_image(filename):
                warnings.append(f"전극사진 {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
                continue
            try:
                cell = ws.cell(row=20, column=3 + idx).coordinate  # C20부터 오른쪽
                place_image(ws, path, cell, *INJATABLE_ELECTRODE_SIZE)
            except Exception as e:
                warnings.append(f"전극사진 {filename} 삽입 실패: {e}")

        for idx, (filename, path) in enumerate(mold_paths):
            if not is_allowed_image(filename):
                warnings.append(f"금형사진 {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
                continue
            try:
                cell = ws.cell(row=58, column=8 + idx).coordinate  # H58부터 오른쪽
                place_image(ws, path, cell, *INJATABLE_MOLD_SIZE)
            except Exception as e:
                warnings.append(f"금형사진 {filename} 삽입 실패: {e}")

        if product_file and product_file.filename:
            if is_allowed_image(product_file.filename):
                product_path = save_upload(product_file, tmp_dir)
                try:
                    place_image(ws, product_path, "C58", *INJATABLE_PRODUCT_SIZE)
                except Exception as e:
                    warnings.append(f"제품사진 삽입 실패: {e}")
            else:
                warnings.append("제품사진: 지원하지 않는 이미지 형식이라 삽입하지 않았습니다.")

        base_name = os.path.splitext(excel_file.filename)[0]
        download_name = sanitize_filename(f"{base_name}_updated.xlsx")
        try:
            return send_workbook(wb, download_name, warnings)
        except Exception as e:
            return jsonify({"error": f"엑셀 저장에 실패했습니다: {type(e).__name__} - {e}"}), 500


# ====================================================================
# 3) SL 웹서버 QCS 승인원 자동화
# ====================================================================
QCS_NAMEPLATE_SIZE = (620, 330)
QCS_HOTRUNNER_SIZE = (280, 450)
QCS_MOLD_OPEN_SIZE = (520, 370)
QCS_MOLD_CLOSE_SIZE = (600, 450)
QCS_ELECTRODE_SIZE = (280, 220)
QCS_ELECTRODE_OFFSET_X = 290
QCS_ELECTRODE_OFFSET_Y = 230


def qcs_insert_horizontal(ws, paths, start_cell, size, offset_x, warnings, label):
    w, h = size
    for idx, (filename, path) in enumerate(paths):
        if not is_allowed_image(filename):
            warnings.append(f"{label} {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
            continue
        try:
            place_image(ws, path, start_cell, w, h, dx_px=idx * offset_x)
        except Exception as e:
            warnings.append(f"{label} {filename} 삽입 실패: {e}")


def qcs_insert_electrode_grid(ws, paths, warnings):
    w, h = QCS_ELECTRODE_SIZE
    for idx, (filename, path) in enumerate(paths):
        if not is_allowed_image(filename):
            warnings.append(f"전극사진 {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
            continue
        row, col = divmod(idx, 4)
        try:
            place_image(ws, path, "D4", w, h, dx_px=col * QCS_ELECTRODE_OFFSET_X, dy_px=row * QCS_ELECTRODE_OFFSET_Y)
        except Exception as e:
            warnings.append(f"전극사진 {filename} 삽입 실패: {e}")


@app.route("/sl-qcs")
def page_sl_qcs():
    return render_template("sl_qcs.html")


@app.route("/sl-qcs/generate", methods=["POST"])
def api_sl_qcs_generate():
    excel_file = request.files.get("excel_file")
    if not excel_file or not excel_file.filename:
        return jsonify({"error": "승인원 엑셀 파일을 업로드해주세요."}), 400
    if not excel_file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "엑셀 파일(.xlsx)만 업로드할 수 있습니다."}), 400

    warnings = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = save_upload(excel_file, tmp_dir)
        try:
            wb = load_workbook(excel_path)
        except Exception as e:
            return jsonify({"error": f"엑셀 파일을 열 수 없습니다: {type(e).__name__} - {e}"}), 400

        if len(wb.worksheets) < 6:
            return jsonify({"error": "이 엑셀 파일은 시트가 6개 미만이라 이 도구의 템플릿과 맞지 않습니다."}), 400

        sheet3 = wb.worksheets[2]
        sheet4 = wb.worksheets[3]
        sheet5 = wb.worksheets[4]
        sheet6 = wb.worksheets[5]

        nameplate_paths = save_uploads_sorted(request.files.getlist("nameplate_images"), tmp_dir)
        hotrunner_paths = save_uploads_sorted(request.files.getlist("hotrunner_images"), tmp_dir)
        mold_open_paths = save_uploads_sorted(request.files.getlist("mold_open_images"), tmp_dir)
        mold_close_paths = save_uploads_sorted(request.files.getlist("mold_close_images"), tmp_dir)
        electrode_paths = save_uploads_sorted(request.files.getlist("electrode_images"), tmp_dir)
        material_file = request.files.get("material_excel")

        qcs_insert_horizontal(sheet3, nameplate_paths, "D4", QCS_NAMEPLATE_SIZE, QCS_NAMEPLATE_SIZE[0] + 20, warnings, "금형 명판사진")
        qcs_insert_horizontal(sheet3, hotrunner_paths, "D31", QCS_HOTRUNNER_SIZE, QCS_HOTRUNNER_SIZE[0] + 10, warnings, "핫런너 명판사진")
        qcs_insert_horizontal(sheet4, mold_open_paths, "D4", QCS_MOLD_OPEN_SIZE, QCS_MOLD_OPEN_SIZE[0] + 20, warnings, "금형 열린사진")
        qcs_insert_horizontal(sheet4, mold_close_paths, "D31", QCS_MOLD_CLOSE_SIZE, QCS_MOLD_CLOSE_SIZE[0] + 20, warnings, "금형 닫힌사진")
        qcs_insert_electrode_grid(sheet5, electrode_paths, warnings)

        if material_file and material_file.filename:
            if material_file.filename.lower().endswith((".xlsx", ".xls")):
                material_path = save_upload(material_file, tmp_dir)
                try:
                    src_wb = load_workbook(material_path, data_only=True)
                    copy_sheet_contents(src_wb.active, sheet6)
                    src_wb.close()
                except Exception as e:
                    warnings.append(f"금형자재표 반영 실패: {e}")
            else:
                warnings.append("금형자재표: 엑셀 파일(.xlsx/.xls)만 지원합니다.")

        wb.active = 0
        base_name = os.path.splitext(excel_file.filename)[0]
        download_name = sanitize_filename(f"{base_name}_updated.xlsx")
        try:
            return send_workbook(wb, download_name, warnings)
        except Exception as e:
            return jsonify({"error": f"엑셀 저장에 실패했습니다: {type(e).__name__} - {e}"}), 500


# ====================================================================
# 4) SL 엑셀파일 승인원 자동화 (전체 버전 - 금형/전극/습합/충진밸런스 사진 +
#    3D스캐너 PDF + 사출조건표/금형자재표 반영)
# ====================================================================
FULL_MOLD_SIZE = (110, 110)
FULL_ELECTRODE_SIZE = (85, 85)
FULL_FUSION_SIZE = (350, 350)
FULL_PDF_SIZE = (710, 380)
FULL_PDF_LH_RH_CROP_RECT = (73, 175, 1655, 1125)
FULL_PDF_3D_CROP_RECT = (8, 7, 1680, 1190)
FULL_PDF_3D_SIZE = (700, 400)
FULL_GOLD_GUIDE_SIZE = (500, 700)
FULL_BALANCE_SIZE = (160, 150)

FULL_MOLD_POSITIONS = {"1": "J14", "2": "J23", "3": "M23", "4": "I6", "5": "M6"}
FULL_FUSION_POSITIONS = {"1": "F11", "2": "B42", "3": "J42", "4": "B74", "5": "J74"}
FULL_BALANCE_POSITIONS = {"1": "A11", "2": "F11", "3": "J11", "4": "N11"}

FULL_ELECTRODE_OFFSET_X = 30
FULL_THREED_OFFSET_X = 50


def full_files_sorted(file_list, tmp_dir):
    """save_uploads_sorted과 동일하지만 이미지가 아닌 파일(PDF 등)도 허용."""
    return save_uploads_sorted(file_list, tmp_dir)


def full_insert_by_prefix(ws, files, positions, size, warnings, label):
    w, h = size
    for key, cell in positions.items():
        match = next((f for f in files if f[0].startswith(key)), None)
        if not match:
            warnings.append(f"{label}: {key}번 파일을 찾을 수 없습니다.")
            continue
        filename, path = match
        if not is_allowed_image(filename):
            warnings.append(f"{label} {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
            continue
        try:
            place_image(ws, path, cell, w, h)
        except Exception as e:
            warnings.append(f"{label} {filename} 삽입 실패: {e}")


def full_insert_side_by_side(ws, files, start_cell, size, offset_x, warnings, label):
    w, h = size
    for idx, (filename, path) in enumerate(files):
        if not is_allowed_image(filename):
            warnings.append(f"{label} {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
            continue
        try:
            place_image(ws, path, start_cell, w, h, dx_px=idx * offset_x)
        except Exception as e:
            warnings.append(f"{label} {filename} 삽입 실패: {e}")


def full_insert_balance(ws, files, warnings):
    w, h = FULL_BALANCE_SIZE
    matched = {}
    unmatched = []
    for filename, path in files:
        found_key = next((k for k in FULL_BALANCE_POSITIONS if filename.startswith(k) and k not in matched), None)
        if found_key:
            matched[found_key] = (filename, path)
        else:
            unmatched.append((filename, path))

    for key, cell in FULL_BALANCE_POSITIONS.items():
        if key not in matched:
            continue
        filename, path = matched[key]
        if not is_allowed_image(filename):
            warnings.append(f"충진밸런스 {filename}: 지원하지 않는 이미지 형식이라 건너뛰었습니다.")
            continue
        try:
            place_image(ws, path, cell, w, h)
        except Exception as e:
            warnings.append(f"충진밸런스 {filename} 삽입 실패: {e}")

    empty_cells = [cell for key, cell in FULL_BALANCE_POSITIONS.items() if key not in matched]
    for (filename, path), cell in zip(unmatched, empty_cells):
        if not is_allowed_image(filename):
            continue
        try:
            place_image(ws, path, cell, w, h)
        except Exception as e:
            warnings.append(f"충진밸런스 추가파일 {filename} 삽입 실패: {e}")


def full_insert_pdf_all_pages(ws, pdf_path, start_cell, crop_rect, size, offset_x, tmp_dir, warnings, label):
    import pymupdf
    w, h = size
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        warnings.append(f"{label}: PDF를 열 수 없습니다 ({type(e).__name__}: {e})")
        return
    for i, page in enumerate(doc):
        try:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            img = PILImage.open(io.BytesIO(pix.tobytes("png")))
            cropped = img.crop(crop_rect)
            out_path = os.path.join(tmp_dir, f"pdf_{uuid.uuid4().hex}.png")
            cropped.save(out_path)
            place_image(ws, out_path, start_cell, w, h, dx_px=i * offset_x)
        except Exception as e:
            warnings.append(f"{label} 페이지 {i + 1} 삽입 실패: {e}")
    doc.close()


@app.route("/sl-approval-full")
def page_sl_approval_full():
    return render_template("sl_approval_full.html")


@app.route("/sl-approval-full/generate", methods=["POST"])
def api_sl_approval_full_generate():
    excel_file = request.files.get("excel_file")
    if not excel_file or not excel_file.filename:
        return jsonify({"error": "승인원 엑셀 파일을 업로드해주세요."}), 400
    if not excel_file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "엑셀 파일(.xlsx)만 업로드할 수 있습니다."}), 400

    warnings = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = save_upload(excel_file, tmp_dir)
        try:
            wb = load_workbook(excel_path)
        except Exception as e:
            return jsonify({"error": f"엑셀 파일을 열 수 없습니다: {type(e).__name__} - {e}"}), 400

        if len(wb.worksheets) < 15:
            return jsonify({"error": "이 엑셀 파일은 시트가 15개 미만이라 이 도구의 템플릿과 맞지 않습니다."}), 400

        sheet4 = wb.worksheets[3]    # 금형제작시방서
        sheet5 = wb.worksheets[4]    # 금형/전극
        sheet9 = wb.worksheets[8]    # LH
        sheet10 = wb.worksheets[9]   # RH
        sheet11 = wb.worksheets[10]  # 충진밸런스
        sheet12 = wb.worksheets[11]  # 3D 전체
        sheet13 = wb.worksheets[12]  # 습합
        sheet14 = wb.worksheets[13]  # 사출조건표
        sheet15 = wb.worksheets[14]  # 금형자재표

        mold_files = full_files_sorted(request.files.getlist("mold_images"), tmp_dir)
        electrode_files = full_files_sorted(request.files.getlist("electrode_images"), tmp_dir)
        fusion_files = full_files_sorted(request.files.getlist("fusion_images"), tmp_dir)
        balance_files = full_files_sorted(request.files.getlist("balance_images"), tmp_dir)
        lhrh_pdf_files = full_files_sorted(request.files.getlist("lhrh_pdfs"), tmp_dir)
        pdf3d_files = full_files_sorted(request.files.getlist("pdf3d_files"), tmp_dir)
        gold_guide_file = request.files.get("gold_guide_image")
        injection_excel_file = request.files.get("injection_excel")
        material_excel_file = request.files.get("material_excel")

        full_insert_by_prefix(sheet5, mold_files, FULL_MOLD_POSITIONS, FULL_MOLD_SIZE, warnings, "금형사진")
        full_insert_side_by_side(sheet5, electrode_files, "J34", FULL_ELECTRODE_SIZE, FULL_ELECTRODE_OFFSET_X, warnings, "전극사진")
        full_insert_by_prefix(sheet13, fusion_files, FULL_FUSION_POSITIONS, FULL_FUSION_SIZE, warnings, "습합사진")
        full_insert_balance(sheet11, balance_files, warnings)

        for filename, path in lhrh_pdf_files:
            lower_name = filename.lower()
            if "lh" in lower_name:
                full_insert_pdf_all_pages(sheet9, path, "C6", FULL_PDF_LH_RH_CROP_RECT, FULL_PDF_SIZE, FULL_THREED_OFFSET_X, tmp_dir, warnings, f"LH PDF({filename})")
            elif "rh" in lower_name:
                full_insert_pdf_all_pages(sheet10, path, "C6", FULL_PDF_LH_RH_CROP_RECT, FULL_PDF_SIZE, FULL_THREED_OFFSET_X, tmp_dir, warnings, f"RH PDF({filename})")
            else:
                warnings.append(f"{filename}: 파일명에 'LH' 또는 'RH'가 없어 어느 시트에 넣을지 알 수 없습니다.")

        for filename, path in pdf3d_files:
            full_insert_pdf_all_pages(sheet12, path, "B8", FULL_PDF_3D_CROP_RECT, FULL_PDF_3D_SIZE, FULL_THREED_OFFSET_X, tmp_dir, warnings, f"3D 측정서({filename})")

        if gold_guide_file and gold_guide_file.filename:
            if is_allowed_image(gold_guide_file.filename):
                gold_guide_path = save_upload(gold_guide_file, tmp_dir)
                try:
                    place_image(sheet4, gold_guide_path, "B4", *FULL_GOLD_GUIDE_SIZE)
                except Exception as e:
                    warnings.append(f"금형제작시방서 삽입 실패: {e}")
            else:
                warnings.append("금형제작시방서: 지원하지 않는 이미지 형식입니다.")

        for label, file_storage, target_sheet in (
            ("사출조건표", injection_excel_file, sheet14),
            ("금형자재표", material_excel_file, sheet15),
        ):
            if file_storage and file_storage.filename:
                if file_storage.filename.lower().endswith((".xlsx", ".xls")):
                    path = save_upload(file_storage, tmp_dir)
                    try:
                        src_wb = load_workbook(path, data_only=True)
                        copy_sheet_contents(src_wb.active, target_sheet)
                        src_wb.close()
                    except Exception as e:
                        warnings.append(f"{label} 반영 실패: {e}")
                else:
                    warnings.append(f"{label}: 엑셀 파일(.xlsx/.xls)만 지원합니다.")

        base_name = os.path.splitext(excel_file.filename)[0]
        counter = 1
        download_name = sanitize_filename(f"{base_name}_updated.xlsx")
        try:
            return send_workbook(wb, download_name, warnings)
        except Exception as e:
            return jsonify({"error": f"엑셀 저장에 실패했습니다: {type(e).__name__} - {e}"}), 500


# ====================================================================
# 5) SL 팩터검증템플릿 제목수정자동화 v3.0 (PPTX 제목 MP번호/품명 치환)
# ====================================================================
@app.route("/sl-factor-template")
def page_sl_factor_template():
    return render_template("sl_factor_template.html")


@app.route("/sl-factor-template/generate", methods=["POST"])
def api_sl_factor_template_generate():
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Pt

    pptx_file = request.files.get("pptx_file")
    if not pptx_file or not pptx_file.filename:
        return jsonify({"error": "PPTX 파일을 업로드해주세요."}), 400
    if not pptx_file.filename.lower().endswith(".pptx"):
        return jsonify({"error": "PPTX 파일(.pptx)만 업로드할 수 있습니다."}), 400

    mp_front = (request.form.get("mp_front") or "").strip()
    mp_back = (request.form.get("mp_back") or "").strip()
    product_name = (request.form.get("product_name") or "").strip()

    if not re.match(r"^\d{2}$", mp_front):
        return jsonify({"error": "MP 앞자리는 숫자 2자리여야 합니다."}), 400
    if not re.match(r"^\d{1,3}$", mp_back):
        return jsonify({"error": "MP 뒷자리는 숫자 1~3자리여야 합니다."}), 400
    if not product_name:
        return jsonify({"error": "품명을 입력해주세요."}), 400

    mp_number = f" MP{mp_front}-{mp_back}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        pptx_path = save_upload(pptx_file, tmp_dir)
        try:
            prs = Presentation(pptx_path)
        except Exception as e:
            return jsonify({"error": f"PPTX 파일을 열 수 없습니다: {type(e).__name__} - {e}"}), 400

        pattern = re.compile(r"MP\d{2}-\d{3}(?:\s+\(.*?\)|\s+[^–\n]*)")
        replaced_count = 0
        for slide in prs.slides:
            for shape in slide.shapes:
                if not (shape.has_text_frame and shape.text.strip()):
                    continue
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if not pattern.search(text):
                        continue
                    rest_text = re.split(r"–", text, maxsplit=1)[-1].strip() if "–" in text else ""
                    paragraph.clear()

                    run1 = paragraph.add_run()
                    run1.text = f"{mp_number} "
                    run1.font.size = Pt(22)

                    run2 = paragraph.add_run()
                    run2.text = product_name
                    run2.font.color.rgb = RGBColor(0, 102, 204)
                    run2.font.size = Pt(22)

                    if rest_text:
                        run3 = paragraph.add_run()
                        run3.text = f" – {rest_text}"
                        run3.font.size = Pt(22)
                    replaced_count += 1

        warnings = []
        if replaced_count == 0:
            warnings.append("MP번호 패턴(MP00-000 ...)을 가진 제목을 찾지 못해 아무 것도 바뀌지 않았습니다.")

        safe_product_name = re.sub(r'[<>:"/\\|?*]', "", product_name)
        download_name = sanitize_filename(f"{mp_number.strip()} {safe_product_name}_팩터검증템플릿_250000(MK-TECH).pptx")

        buf = io.BytesIO()
        try:
            prs.save(buf)
        except Exception as e:
            return jsonify({"error": f"PPTX 저장에 실패했습니다: {type(e).__name__} - {e}"}), 500
        buf.seek(0)

        response = send_file(
            buf,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        if warnings:
            import base64
            encoded = base64.b64encode("\n".join(warnings).encode("utf-8")).decode("ascii")
            response.headers["X-Warnings-B64"] = encoded
        response.headers["Access-Control-Expose-Headers"] = "X-Warnings-B64"
        return response


if __name__ == "__main__":
    from waitress import serve

    print("설계 서류업무 자동화 허브 시작: http://192.168.134.130:8001")
    serve(app, host="0.0.0.0", port=8001)
