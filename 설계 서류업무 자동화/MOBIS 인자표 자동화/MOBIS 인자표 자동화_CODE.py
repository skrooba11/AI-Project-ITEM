import os
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
import xlwings as xw

# 이미지 크기 설정
ELECTRODE_WIDTH, ELECTRODE_HEIGHT = 80, 80
MOLD_WIDTH, MOLD_HEIGHT = 90, 90
PRODUCT_WIDTH, PRODUCT_HEIGHT = 110, 110

# 저장 파일명 자동 생성
def generate_versioned_filename(base_path):
    base, ext = os.path.splitext(base_path)
    candidate = base + "_updated" + ext
    counter = 2
    while os.path.exists(candidate):
        candidate = f"{base}_updated_rev{counter}{ext}"
        counter += 1
    return candidate

# 임시 폴더로 이미지 복사 (안전한 경로 확보)
def safe_image_path(original_path, temp_files):
    temp_dir = tempfile.gettempdir()
    filename = os.path.basename(original_path)
    safe_path = os.path.join(temp_dir, filename)
    shutil.copy2(original_path, safe_path)
    temp_files.append(safe_path)
    return safe_path

# 이미지 삽입 함수
def insert_images_with_xlwings(excel_path, electrode_folder=None, mold_folder=None, product_img=None):
    temp_files = []
    app = xw.App(visible=False)
    try:
        wb = app.books.open(excel_path)
        ws = wb.sheets[0]

        # 전극사진 (C20부터 오른쪽)
        if electrode_folder:
            files = sorted([
                f for f in os.listdir(electrode_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ])
            for idx, fname in enumerate(files):
                original = os.path.join(electrode_folder, fname)
                if not os.path.exists(original): continue
                img_path = safe_image_path(original, temp_files)
                try:
                    cell = ws.range((20, 3 + idx))  # C20 = (20,3)
                    ws.pictures.add(img_path, left=cell.left, top=cell.top,
                                    width=ELECTRODE_WIDTH, height=ELECTRODE_HEIGHT)
                    print(f"✅ 전극사진 {cell.address} 삽입 완료: {fname}")
                except Exception as e:
                    print(f"❌ 전극사진 삽입 실패: {fname} → {e}")

        # 금형사진 (H58부터 오른쪽)
        if mold_folder:
            files = sorted([
                f for f in os.listdir(mold_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ])
            for idx, fname in enumerate(files):
                original = os.path.join(mold_folder, fname)
                if not os.path.exists(original): continue
                img_path = safe_image_path(original, temp_files)
                try:
                    cell = ws.range((58, 8 + idx))  # H58 = (58,8)
                    ws.pictures.add(img_path, left=cell.left, top=cell.top,
                                    width=MOLD_WIDTH, height=MOLD_HEIGHT)
                    print(f"✅ 금형사진 {cell.address} 삽입 완료: {fname}")
                except Exception as e:
                    print(f"❌ 금형사진 삽입 실패: {fname} → {e}")

        # 제품사진 (C58)
        if product_img and os.path.exists(product_img):
            img_path = safe_image_path(product_img, temp_files)
            try:
                cell = ws.range("C58")
                ws.pictures.add(img_path, left=cell.left, top=cell.top,
                                width=PRODUCT_WIDTH, height=PRODUCT_HEIGHT)
                print(f"✅ 제품사진 {cell.address} 삽입 완료")
            except Exception as e:
                print(f"❌ 제품사진 삽입 실패: {product_img} → {e}")

        # 저장 및 종료
        save_path = generate_versioned_filename(excel_path)
        wb.save(save_path)
        wb.close()
        app.quit()

        # 임시 이미지 삭제
        for f in temp_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"⚠ 임시파일 삭제 실패: {f} → {e}")

        # 탐색기 열기
        try:
            os.startfile(os.path.dirname(save_path))
        except Exception as e:
            print(f"⚠ 탐색기 열기 실패: {e}")

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("완료", f"✅ 이미지 삽입 완료!\n→ {os.path.basename(save_path)}\n📁 폴더가 열렸습니다.")
        root.destroy()
    except Exception as e:
        app.quit()
        messagebox.showerror("실행 오류", f"엑셀 작업 중 오류 발생:\n{e}")

# GUI 실행
def select_and_run():
    root = tk.Tk()
    root.withdraw()

    excel_file = filedialog.askopenfilename(
        title="인자표 파일 선택", filetypes=[("Excel Files", "*.xlsx")]
    )
    if not excel_file:
        return

    electrode_folder = filedialog.askdirectory(title="전극사진 폴더 선택")
    mold_folder = filedialog.askdirectory(title="금형사진 폴더 선택")
    product_img = filedialog.askopenfilename(
        title="제품사진 선택", filetypes=[("Image files", "*.png *.jpg *.jpeg")]
    )

    insert_images_with_xlwings(excel_file, electrode_folder, mold_folder, product_img)

if __name__ == "__main__":
    select_and_run()
