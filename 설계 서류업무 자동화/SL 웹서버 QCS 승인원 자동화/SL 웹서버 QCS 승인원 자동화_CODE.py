import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import xlwings as xw
from PIL import Image as PILImage
from pathlib import Path
import traceback

# 이미지 크기 설정
NAMEPLATE_IMAGE_WIDTH, NAMEPLATE_IMAGE_HEIGHT = 620, 330  # 금형 명판사진 (D4부터)
HOTRUNNER_IMAGE_WIDTH, HOTRUNNER_IMAGE_HEIGHT = 280, 450  # 핫런너 명판사진 (D31부터)
MOLD_OPEN_IMAGE_WIDTH, MOLD_OPEN_IMAGE_HEIGHT = 520, 370  # 금형 열린사진 (D4부터)
MOLD_CLOSE_IMAGE_WIDTH, MOLD_CLOSE_IMAGE_HEIGHT = 600, 450  # 금형 닫힌사진 (D31부터)
ELECTRODE_IMAGE_WIDTH, ELECTRODE_IMAGE_HEIGHT = 280, 220  # 전극사진 (D4부터)

# 전극사진 오프셋 (나란히 정렬을 위한 간격)
ELECTRODE_OFFSET_X = 290
ELECTRODE_OFFSET_Y = 230

def insert_single_image(sheet, image_path, target_cell, width, height):
    """단일 이미지 삽입"""
    if not image_path:
        return
    
    temp_dir = Path("temp_img")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        with PILImage.open(image_path) as img:
            img = img.convert("RGB")
            temp_path = temp_dir / f"{Path(image_path).stem}_converted.png"
            img.save(temp_path, format="PNG")
            
            cell = sheet.range(target_cell)
            sheet.pictures.add(str(temp_path.resolve()), 
                             left=cell.left, top=cell.top,
                             width=width, height=height)
            print(f"✅ {Path(image_path).name} → {target_cell} 삽입 완료")
    except Exception as e:
        print(f"❌ 이미지 삽입 오류 ({image_path}): {e}")

def insert_multiple_images_horizontal(sheet, image_paths, start_cell, width, height, offset_x):
    """여러 이미지를 가로로 나란히 삽입"""
    if not image_paths:
        return
    
    temp_dir = Path("temp_img")
    temp_dir.mkdir(exist_ok=True)
    
    cell = sheet.range(start_cell)
    base_left = cell.left
    top = cell.top
    
    for idx, image_path in enumerate(image_paths):
        try:
            with PILImage.open(image_path) as img:
                img = img.convert("RGB")
                temp_path = temp_dir / f"{Path(image_path).stem}_{idx}.png"
                img.save(temp_path, format="PNG")
                
                sheet.pictures.add(str(temp_path.resolve()),
                                 left=base_left + idx * offset_x, top=top,
                                 width=width, height=height)
                print(f"✅ {Path(image_path).name} → {start_cell}(+{idx}) 삽입 완료")
        except Exception as e:
            print(f"❌ 이미지 삽입 오류 ({image_path}): {e}")

def insert_electrode_images(sheet, image_paths, width, height):
    """전극사진 삽입 (4장씩 가로 정렬, 초과시 다음 줄)"""
    if not image_paths:
        return
    
    temp_dir = Path("temp_img")
    temp_dir.mkdir(exist_ok=True)
    
    start_cell = sheet.range("D4")
    base_left = start_cell.left
    base_top = start_cell.top
    
    for idx, image_path in enumerate(image_paths):
        try:
            with PILImage.open(image_path) as img:
                img = img.convert("RGB")
                temp_path = temp_dir / f"electrode_{idx}.png"
                img.save(temp_path, format="PNG")
                
                # 4장씩 가로 정렬, 초과시 다음 줄
                row = idx // 4
                col = idx % 4
                
                left = base_left + col * ELECTRODE_OFFSET_X
                top = base_top + row * ELECTRODE_OFFSET_Y
                
                sheet.pictures.add(str(temp_path.resolve()),
                                 left=left, top=top,
                                 width=width, height=height)
                print(f"✅ 전극사진 {Path(image_path).name} → 위치({row},{col}) 삽입 완료")
        except Exception as e:
            print(f"❌ 전극사진 삽입 오류 ({image_path}): {e}")

def insert_excel_sheet_from_file(target_sheet, source_excel_path):
    """엑셀 시트 전체 복사해서 붙여넣기 (서식 유지)"""
    if not source_excel_path:
        return
    try:
        src_wb = xw.Book(source_excel_path)
        src_sheet = src_wb.sheets[0]  # 첫 번째 시트
        
        # 대상 시트 초기화
        target_sheet.clear()
        
        # 전체 시트 복사 및 붙여넣기 (서식 유지)
        src_sheet.api.Cells.Copy()
        target_sheet.api.Cells.PasteSpecial(Paste=-4104)  # xlPasteAll (값과 서식 모두)
        target_sheet.api.Application.CutCopyMode = False  # 복사 모드 해제
        
        print(f"✅ 시트 전체 복사 완료 (서식 유지): {source_excel_path}")
        src_wb.close()
    except Exception as e:
        print(f"❌ 시트 복사 오류: {e}")

def select_excel_file(title):
    """엑셀 파일 선택"""
    filetypes = [("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
    file = filedialog.askopenfilename(title=title, filetypes=filetypes)
    return file if file else None

def select_multiple_images(title):
    """여러 이미지 파일 선택"""
    filetypes = [("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All Files", "*.*")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes)
    return list(files) if files else []

def select_single_image(title):
    """단일 이미지 파일 선택"""
    filetypes = [("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All Files", "*.*")]
    file = filedialog.askopenfilename(title=title, filetypes=filetypes)
    return file if file else None

def run():
    """메인 실행 함수"""
    root = tk.Tk()
    root.withdraw()

    # 1. 승인원 엑셀 파일 선택
    excel_path = filedialog.askopenfilename(
        title="승인원 엑셀 파일 선택", 
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
    )
    if not excel_path:
        messagebox.showwarning("경고", "엑셀 파일을 선택하지 않았습니다.")
        return

    # 2. 금형 명판사진 선택 (다중 선택)
    nameplate_images = select_multiple_images("금형 명판사진 선택 (3시트용)")
    
    # 3. 핫런너 명판사진 선택 (다중 선택)
    hotrunner_images = select_multiple_images("핫런너 명판사진 선택 (3시트용)")
    
    # 4. 금형 열린사진 선택 (다중 선택)
    mold_open_images = select_multiple_images("금형 열린사진 선택 (4시트용)")
    
    # 5. 금형 닫힌사진 선택 (다중 선택)
    mold_close_images = select_multiple_images("금형 닫힌사진 선택 (4시트용)")
    
    # 6. 전극사진 선택 (다중 선택)
    electrode_images = select_multiple_images("전극사진 선택 (5시트용)")

    # 7. 금형자재표 엑셀 파일 선택
    material_excel = select_excel_file("금형자재표 엑셀 파일 선택 (6시트용)")

    # 저장 위치 및 파일명 선택
    save_path = filedialog.asksaveasfilename(
        title="승인원 파일 저장 위치 및 파일명 지정",
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        initialdir=os.path.dirname(excel_path)
    )
    if not save_path:
        messagebox.showwarning("경고", "저장 위치를 지정하지 않았습니다.")
        return

    # 파일 복사
    shutil.copyfile(excel_path, save_path)

    # Excel 작업 시작
    app = xw.App(visible=False)
    try:
        wb = app.books.open(save_path)
        app.display_alerts = False

        # temp 폴더 생성
        temp_dir = Path("temp_img")
        temp_dir.mkdir(exist_ok=True)

        print("🚀 이미지 삽입 작업 시작...")

        # 3시트(명판사진) 작업
        sheet3 = wb.sheets[2]  # 0-based index, 3번째 시트
        
        # 금형 명판사진 삽입 (D4부터 가로 나란히)
        if nameplate_images:
            insert_multiple_images_horizontal(sheet3, nameplate_images, "D4", 
                                            NAMEPLATE_IMAGE_WIDTH, NAMEPLATE_IMAGE_HEIGHT,
                                            NAMEPLATE_IMAGE_WIDTH + 20)
        else:
            print("ℹ️ 금형 명판사진이 선택되지 않았습니다.")

        # 핫런너 명판사진 삽입 (D31부터 가로 나란히)
        if hotrunner_images:
            insert_multiple_images_horizontal(sheet3, hotrunner_images, "D31",
                                            HOTRUNNER_IMAGE_WIDTH, HOTRUNNER_IMAGE_HEIGHT, 
                                            HOTRUNNER_IMAGE_WIDTH + 10)
        else:
            print("ℹ️ 핫런너 명판사진이 선택되지 않았습니다.")

        # 4시트(금형사진) 작업
        sheet4 = wb.sheets[3]  # 0-based index, 4번째 시트
        
        # 금형 열린사진 삽입 (D4부터 가로 나란히)
        if mold_open_images:
            insert_multiple_images_horizontal(sheet4, mold_open_images, "D4",
                                            MOLD_OPEN_IMAGE_WIDTH, MOLD_OPEN_IMAGE_HEIGHT,
                                            MOLD_OPEN_IMAGE_WIDTH + 20)
        else:
            print("ℹ️ 금형 열린사진이 선택되지 않았습니다.")

        # 금형 닫힌사진 삽입 (D31부터 가로 나란히)
        if mold_close_images:
            insert_multiple_images_horizontal(sheet4, mold_close_images, "D31",
                                            MOLD_CLOSE_IMAGE_WIDTH, MOLD_CLOSE_IMAGE_HEIGHT,
                                            MOLD_CLOSE_IMAGE_WIDTH + 20)
        else:
            print("ℹ️ 금형 닫힌사진이 선택되지 않았습니다.")

        # 5시트(전극사진) 작업
        sheet5 = wb.sheets[4]  # 0-based index, 5번째 시트
        
        # 전극사진 삽입 (4장씩 가로 정렬, 초과시 다음 줄)
        if electrode_images:
            insert_electrode_images(sheet5, electrode_images, 
                                  ELECTRODE_IMAGE_WIDTH, ELECTRODE_IMAGE_HEIGHT)
        else:
            print("ℹ️ 전극사진이 선택되지 않았습니다.")

        # 6시트(금형자재표) 작업
        sheet6 = wb.sheets[5]  # 0-based index, 6번째 시트
        
        # 금형자재표 엑셀 파일 복사
        if material_excel:
            insert_excel_sheet_from_file(sheet6, material_excel)
        else:
            print("ℹ️ 금형자재표 엑셀 파일이 선택되지 않았습니다.")

        # 1시트를 활성 시트로 설정
        wb.sheets[0].activate()

        # 저장 및 종료
        wb.save()
        wb.close()
        app.quit()

        # 임시 폴더 정리
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        # 완료된 파일 폴더 열기
        os.startfile(os.path.dirname(save_path))
        
        print(f"🎉 작업 완료 → {save_path}")

    except Exception as e:
        app.quit()
        print("❌ 예외 발생:", e)
        print(traceback.format_exc())
        messagebox.showerror("오류 발생", f"작업 중 오류가 발생했습니다:\n{str(e)}")
        
        # 오류 시에도 임시 폴더 정리
        if Path("temp_img").exists():
            shutil.rmtree(Path("temp_img"))

if __name__ == "__main__":
    run()