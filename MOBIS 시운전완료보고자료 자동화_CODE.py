import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from copy import copy


PHOTO_POSITIONS = {'mold_1': 'M5', 'mold_2': 'B6', 'mold_3': 'B22', 'product': 'L23'}

# 사이즈 설정 (px 기준) - 필요시 수정
IMAGE_SIZES = {
    'mold_1': (350, 240),   # 금형 1번
    'mold_2': (500, 300),   # 금형 2번
    'mold_3': (500, 300),   # 금형 3번
    'product': (500, 300),  # 제품 사진
}

def choose_mold_type():
    choice = {'value': None}
    def set_choice(val): choice['value'] = val; window.destroy()
    window = tk.Tk(); window.title("금형 종류 선택"); window.geometry("300x150")
    tk.Label(window, text="금형 종류를 선택하세요", font=("맑은 고딕", 12)).pack(pady=20)
    f = tk.Frame(window); f.pack()
    tk.Button(f, text="일반 금형", width=12, height=2, command=lambda: set_choice("일반")).grid(row=0, column=0, padx=10)
    tk.Button(f, text="다색 금형", width=12, height=2, command=lambda: set_choice("다색")).grid(row=0, column=1, padx=10)
    window.mainloop()
    return choice['value']

def select_file(title, types): tk.Tk().withdraw(); return filedialog.askopenfilename(title=title, filetypes=types)
def select_folder(title): tk.Tk().withdraw(); return filedialog.askdirectory(title=title)
def save_file(title, default_name):
    tk.Tk().withdraw()
    return filedialog.asksaveasfilename(
        title=title,
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")],
        initialfile=default_name
    )



def insert_images(ws, images):
    """이미지를 워크시트에 삽입하고 결과를 반환"""
    unsupported_images = []
    failed_images = []
    success_count = 0

    for key, addr in PHOTO_POSITIONS.items():
        path = images.get(key)
        if path and os.path.exists(path):
            try:
                # 파일 확장자 확인
                ext = os.path.splitext(path)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                    print(f"❌ {key} 이미지 형식이 지원되지 않습니다: {ext}")
                    print(f"   지원 형식: .png, .jpg, .jpeg, .bmp, .gif")
                    print(f"   파일: {os.path.basename(path)}")
                    unsupported_images.append((key, os.path.basename(path), ext))
                    continue

                # 파일 크기 확인 (0바이트 파일 체크)
                file_size = os.path.getsize(path)
                if file_size == 0:
                    print(f"⚠ {key} 이미지 파일이 비어있음: {os.path.basename(path)}")
                    failed_images.append((key, os.path.basename(path), "파일이 비어있음"))
                    continue

                # 이미지 크기 확인 및 조정
                img = XLImage(path)

                # 엑셀이 지원하지 않는 내부 포맷(예: 휴대폰 카메라의 MPO,
                # BMP, TIFF 등) 정규화 → openpyxl 저장 시 '.mpo' KeyError 방지
                if str(getattr(img, 'format', '')).lower() not in ('png', 'jpeg', 'gif'):
                    img.format = 'png'

                # 이미지가 제대로 로드되었는지 확인
                if not hasattr(img, '_data') or img._data is None:
                    print(f"⚠ {key} 이미지 로드 실패: {os.path.basename(path)}")
                    failed_images.append((key, os.path.basename(path), "로드 실패"))
                    continue

                img.anchor = ws[addr].coordinate

                if key in IMAGE_SIZES:
                    img.width, img.height = IMAGE_SIZES[key]

                ws.add_image(img)
                print(f"✅ {key} 이미지 삽입 완료 → 위치: {addr}, 파일: {os.path.basename(path)} ({file_size:,} bytes)")
                success_count += 1
            except PermissionError:
                print(f"❌ {key} 이미지 접근 권한 없음: {os.path.basename(path)}")
                failed_images.append((key, os.path.basename(path), "접근 권한 없음"))
            except Exception as e:
                print(f"❌ {key} 이미지 삽입 실패: {type(e).__name__} - {e}")
                print(f"   파일: {path}")
                failed_images.append((key, os.path.basename(path), str(e)))
        else:
            if path:
                print(f"⚠ {key} 이미지 파일을 찾을 수 없음: {path}")
            else:
                print(f"⚠ {key} 이미지가 선택되지 않음")

    return {
        'success_count': success_count,
        'unsupported': unsupported_images,
        'failed': failed_images
    }

def extract_after(text, keyword):
    if not text: return ""
    match = re.search(re.escape(keyword) + r"\s*(.*)", text)
    return match.group(1).strip() if match else ""

def apply_material(ws, mat_path):
    try:
        if not os.path.exists(mat_path):
            print(f"❌ 자재표 파일을 찾을 수 없음: {mat_path}")
            return None

        print(f"📄 자재표 파일 읽는 중: {os.path.basename(mat_path)}")

        wb_mat = load_workbook(mat_path, data_only=True)
        ws_mat = wb_mat.active

        # 안전하게 셀 값 읽기
        def safe_get_cell_value(cell_ref):
            try:
                return ws_mat[cell_ref].value
            except:
                return None

        model = extract_after(safe_get_cell_value('B2'), "*MODEL :")
        mold = extract_after(safe_get_cell_value('F2'), "*금형명 :")
        size = extract_after(safe_get_cell_value('B4'), "*금형 SIZE :")
        weight = extract_after(safe_get_cell_value('F4'), "*금형 중량 :") or extract_after(safe_get_cell_value('B2'), "*금형 중량 :")

        wb_mat.close()

        full_name = f"{model} {mold}".strip()

        if not full_name or full_name == "":
            print(f"⚠ 자재표에서 제품명을 추출할 수 없음")
            full_name = "제품명없음"

        # 셀 값만 변경하고 스타일은 건드리지 않음
        try:
            e3_cell = ws['E3']
            e3_cell.value = f"제품명 : {full_name}"
        except Exception as e:
            print(f"⚠ E3 셀 업데이트 실패: {e}")

        try:
            o15_cell = ws['O15']
            if size:
                o15_cell.value = size
        except Exception as e:
            print(f"⚠ O15 셀 업데이트 실패: {e}")

        try:
            o17_cell = ws['O17']
            if weight:
                o17_cell.value = weight
        except Exception as e:
            print(f"⚠ O17 셀 업데이트 실패: {e}")

        # 시트 이름은 31자로 제한하고 특수문자 제거
        safe_sheet_name = sanitize_filename(full_name[:31])
        # 엑셀 시트 이름에서 추가로 금지된 문자 제거
        safe_sheet_name = re.sub(r'[\[\]\*\?:/\\]', '_', safe_sheet_name)

        try:
            ws.title = safe_sheet_name
        except Exception as e:
            print(f"⚠ 시트 이름 변경 실패: {e}")
            ws.title = "Sheet1"

        print(f"✅ 자재표 적용 완료 → 제품명: {full_name}, SIZE: {size}, 중량: {weight}")
        return full_name
    except Exception as e:
        print(f"❌ 자재표 처리 실패: {type(e).__name__} - {e}")
        import traceback
        print(traceback.format_exc())
        return None

def select_mold_images(prefix=""):
    """금형 사진 3개를 순차적으로 선택

    Args:
        prefix: "1차 " 또는 "2차 " 같은 접두사 (다색 금형용)
    """
    result = {'mold_1': None, 'mold_2': None, 'mold_3': None}

    # 지원되는 이미지 형식만 선택 가능하도록 필터링
    image_types = [
        ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
        ("PNG 파일", "*.png"),
        ("JPEG 파일", "*.jpg;*.jpeg"),
        ("모든 파일", "*.*")
    ]

    # 금형 상측 사진
    mold_1 = select_file(f"{prefix}금형 상측 사진 선택", image_types)
    if mold_1:
        result['mold_1'] = mold_1
        print(f"✅ {prefix}금형 상측 사진 선택: {os.path.basename(mold_1)}")

    # 금형 하측 사진
    mold_2 = select_file(f"{prefix}금형 하측 사진 선택", image_types)
    if mold_2:
        result['mold_2'] = mold_2
        print(f"✅ {prefix}금형 하측 사진 선택: {os.path.basename(mold_2)}")

    # 금형 전체(ASSY) 사진
    mold_3 = select_file(f"{prefix}금형 전체(ASSY) 사진 선택", image_types)
    if mold_3:
        result['mold_3'] = mold_3
        print(f"✅ {prefix}금형 전체(ASSY) 사진 선택: {os.path.basename(mold_3)}")

    return result

def sanitize_filename(filename):
    """파일명에서 엑셀이 지원하지 않는 특수문자 제거"""
    # 엑셀 파일명에서 문제가 될 수 있는 문자들 제거
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # 연속된 공백을 하나로
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # 앞뒤 공백 제거
    sanitized = sanitized.strip()
    return sanitized

def safe_save_workbook(wb, save_path):
    """안전한 워크북 저장 함수"""
    try:
        # 파일명 검증 및 정리
        dir_path = os.path.dirname(save_path)
        file_name = os.path.basename(save_path)
        clean_name = sanitize_filename(file_name)

        if clean_name != file_name:
            print(f"⚠ 파일명에서 특수문자 제거: {file_name} → {clean_name}")
            save_path = os.path.join(dir_path, clean_name)

        # 기존 파일이 있으면 삭제
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                print(f"📝 기존 파일 삭제: {os.path.basename(save_path)}")
            except Exception as e:
                print(f"⚠ 기존 파일 삭제 실패: {e}")
                return False

        # 임시 파일로 먼저 저장
        temp_path = save_path + ".tmp"

        # 워크북 저장 전 최적화
        for ws in wb.worksheets:
            # 계산 설정 초기화
            ws.sheet_properties.tabColor = None

        # 계산 모드를 수동으로 설정하여 저장 속도 향상
        wb.calculation.calcMode = 'manual'

        print(f"💾 파일 저장 중...")

        # 임시 파일로 저장
        wb.save(temp_path)

        # 임시 파일 검증
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            print(f"❌ 임시 파일 저장 실패")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

        # 임시 파일을 최종 파일로 이동
        shutil.move(temp_path, save_path)

        # 최종 파일 검증
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            print(f"✅ 파일 저장 성공: {os.path.basename(save_path)}")
            print(f"📊 파일 크기: {os.path.getsize(save_path):,} bytes")
            return True
        else:
            print(f"❌ 최종 파일 생성 실패")
            return False

    except PermissionError:
        print(f"❌ 저장 실패: 파일에 대한 권한이 없습니다. 파일이 다른 프로그램에서 열려있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 저장 실패: {type(e).__name__} - {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        # 임시 파일이 남아있으면 삭제
        temp_path = save_path + ".tmp" if 'save_path' in locals() else None
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass





def main():
    print("=" * 60)
    print("MOBIS 시운전완료보고자료 자동화 프로그램")
    print("=" * 60)

    mold_type = choose_mold_type()
    if not mold_type:
        print("❌ 금형 종류가 선택되지 않았습니다.")
        return
    print(f"▶ 선택된 금형 종류: {mold_type}")

    excel_path = select_file("시운전보고자료 파일 선택", [("Excel Files", "*.xlsx")])
    if not excel_path:
        print("❌ 엑셀 파일이 선택되지 않았습니다.")
        return

    # 파일 존재 및 접근 가능 여부 확인
    if not os.path.exists(excel_path):
        messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{excel_path}")
        return

    try:
        # 파일 크기 확인
        file_size = os.path.getsize(excel_path)
        print(f"📂 엑셀 파일 크기: {file_size:,} bytes")

        if file_size == 0:
            messagebox.showerror("오류", "엑셀 파일이 비어있습니다.")
            return

        # keep_vba=False로 VBA 코드 제거하여 안정성 향상
        print(f"📂 엑셀 파일 불러오는 중: {os.path.basename(excel_path)}")
        wb = load_workbook(excel_path, keep_vba=False, data_only=False)
        print(f"✅ 엑셀 파일 불러오기 완료")
        print(f"   시트 개수: {len(wb.worksheets)}")
        print(f"   시트 이름: {', '.join([ws.title for ws in wb.worksheets])}")
    except PermissionError:
        messagebox.showerror("오류", f"파일에 대한 권한이 없습니다.\n파일이 다른 프로그램에서 열려있는지 확인하세요:\n{excel_path}")
        return
    except Exception as e:
        messagebox.showerror("오류", f"엑셀 파일을 열 수 없습니다:\n{type(e).__name__}\n{str(e)}")
        print(f"❌ 엑셀 파일 로드 실패: {type(e).__name__} - {e}")
        import traceback
        print(traceback.format_exc())
        return

    if mold_type == "일반":
        ws = wb.active
        imgs = select_mold_images()

        # 제품 사진 선택 (지원 형식 명시)
        image_types = [
            ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
            ("PNG 파일", "*.png"),
            ("JPEG 파일", "*.jpg;*.jpeg"),
            ("모든 파일", "*.*")
        ]
        product_img = select_file("제품사진 선택", image_types)
        material = select_file("금형자재표 파일 선택", [("Excel Files", "*.xlsx")])

        imgs['product'] = product_img
        result = insert_images(ws, imgs)

        # 비지원 이미지가 있으면 경고
        if result['unsupported']:
            msg = "⚠️ 다음 이미지는 지원되지 않는 형식입니다:\n\n"
            for _, filename, ext in result['unsupported']:
                msg += f"- {filename} ({ext})\n"
            msg += "\n지원 형식: .png, .jpg, .jpeg, .bmp, .gif\n"
            msg += "해당 이미지는 엑셀 파일에 포함되지 않습니다."
            messagebox.showwarning("이미지 형식 경고", msg)

        name = apply_material(ws, material) if material else "시트"
        if len(wb.sheetnames) > 1: wb.remove(wb[wb.sheetnames[1]])

    else:
        ws1 = wb.worksheets[0]
        ws2 = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.create_sheet("2차")

        imgs1 = select_mold_images("1차 ")
        imgs2 = select_mold_images("2차 ")

        # 제품 사진 선택 (지원 형식 명시)
        image_types = [
            ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
            ("PNG 파일", "*.png"),
            ("JPEG 파일", "*.jpg;*.jpeg"),
            ("모든 파일", "*.*")
        ]
        product = select_file("1+2차 제품사진 파일 선택", image_types)
        material1 = select_file("1차 금형자재표 파일 선택", [("Excel Files", "*.xlsx")])
        material2 = select_file("2차 금형자재표 파일 선택", [("Excel Files", "*.xlsx")])

        imgs1['product'] = product
        imgs2['product'] = product
        result1 = insert_images(ws1, imgs1)
        result2 = insert_images(ws2, imgs2)

        # 비지원 이미지 통합 경고
        all_unsupported = result1['unsupported'] + result2['unsupported']
        if all_unsupported:
            msg = "⚠️ 다음 이미지는 지원되지 않는 형식입니다:\n\n"
            for _, filename, ext in all_unsupported:
                msg += f"- {filename} ({ext})\n"
            msg += "\n지원 형식: .png, .jpg, .jpeg, .bmp, .gif\n"
            msg += "해당 이미지는 엑셀 파일에 포함되지 않습니다."
            messagebox.showwarning("이미지 형식 경고", msg)

        name = apply_material(ws1, material1) if material1 else "시트1"
        _ = apply_material(ws2, material2)

    # 기본 파일명 생성 (특수문자 제거)
    safe_name = sanitize_filename(name) if name else "시운전보고자료"
    default_filename = f"{safe_name}_설치시운전완료보고자료_MK-TECH.xlsx"

    print(f"\n💾 파일 저장 준비 중...")
    print(f"   기본 파일명: {default_filename}")

    # 파일 저장 대화상자 (사용자가 파일명 지정 가능)
    save_path = save_file("저장 위치 및 파일명 설정", default_filename)
    if not save_path:
        print("❌ 저장이 취소되었습니다.")
        wb.close()
        return

    print(f"   최종 저장 경로: {save_path}")

    # 안전한 저장 시도
    try:
        if safe_save_workbook(wb, save_path):
            wb.close()
            print(f"✅ 모든 작업 완료!")

            # 저장 완료 메시지
            save_dir = os.path.dirname(save_path)
            final_size = os.path.getsize(save_path)

            msg = f"✅ 저장 완료!\n\n"
            msg += f"파일명: {os.path.basename(save_path)}\n"
            msg += f"저장 위치: {save_dir}\n"
            msg += f"파일 크기: {final_size:,} bytes"

            messagebox.showinfo("완료", msg)

            # 저장된 폴더 자동으로 열기
            try:
                os.startfile(save_dir)
            except Exception as e:
                print(f"⚠ 폴더 열기 실패: {e}")

            print("=" * 60)
        else:
            wb.close()
            messagebox.showerror("오류",
                f"파일 저장에 실패했습니다.\n\n"
                f"저장 경로: {save_path}\n\n"
                f"가능한 원인:\n"
                f"1. 파일이 다른 프로그램에서 열려있음\n"
                f"2. 저장 권한이 없는 폴더\n"
                f"3. 디스크 공간 부족\n\n"
                f"터미널 창의 상세 오류 메시지를 확인하세요.")
            return
    except Exception as e:
        wb.close()
        print(f"❌ 저장 중 오류 발생: {type(e).__name__} - {e}")
        import traceback
        print(traceback.format_exc())
        messagebox.showerror("오류", f"저장 중 오류가 발생했습니다:\n{type(e).__name__}\n{str(e)}")
        return

if __name__ == "__main__":
    main() 