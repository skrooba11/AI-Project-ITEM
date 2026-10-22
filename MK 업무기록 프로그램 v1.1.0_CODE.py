# ============================================
# 실시간 업무기록기 프로그램
# ============================================
# 
# 이 프로그램은 실시간으로 업무 작업을 기록하고 관리하는 GUI 프로그램입니다.
# 
# 주요 기능:
# 1. 실시간 업무 시작/종료 기록
# 2. 작업 코드, MK번호, 공정명, 업무내용 관리
# 3. 즐겨찾기 기능 (8개 버튼)
# 4. 로그 추가/편집/삭제 기능
# 5. 엑셀 파일로 내보내기
# 6. 전체/오늘 기록 필터링
# 7. 날짜별 정렬 기능
# 8. 중복 실행 방지
# 
# 개발자: 초보자를 위한 상세 주석 포함
# 버전: 2.0
# ============================================

# 필요한 라이브러리들을 가져오기 (import)
import tkinter as tk                    # GUI 창을 만드는 기본 라이브러리
from tkinter import ttk, messagebox, simpledialog, filedialog  # GUI의 추가 기능들
from tkinter.ttk import Combobox       # 드롭다운 선택박스
# tkcalendar 라이브러리 자동 설치 및 임포트
def install_tkcalendar():
    """tkcalendar 라이브러리 자동 설치"""
    try:
        import subprocess
        import sys
        print("tkcalendar 라이브러리 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkcalendar"])
        print("tkcalendar 라이브러리 설치 완료")
        return True
    except Exception as e:
        print(f"tkcalendar 라이브러리 설치 실패: {e}")
        return False

try:
    from tkcalendar import Calendar     # 캘린더 위젯
    CALENDAR_AVAILABLE = True
    print("캘린더 라이브러리 로드 성공")
except ImportError as e:
    print(f"tkcalendar 라이브러리 로드 실패: {e}")
    print("자동 설치를 시도합니다...")
    if install_tkcalendar():
        try:
            from tkcalendar import Calendar
            CALENDAR_AVAILABLE = True
            print("캘린더 라이브러리 자동 설치 후 로드 성공")
        except ImportError:
            Calendar = None
            CALENDAR_AVAILABLE = False
            print("캘린더 라이브러리 자동 설치 후에도 로드 실패")
    else:
        Calendar = None
        CALENDAR_AVAILABLE = False
        print("캘린더 라이브러리 설치 실패")
from datetime import datetime, timedelta  # 날짜와 시간을 다루는 라이브러리
from PIL import ImageGrab, ImageTk, Image, ImageDraw, ImageFont  # 이미지를 다루는 라이브러리
import pyperclip                        # 클립보드(복사/붙여넣기) 기능
import os                              # 파일과 폴더를 다루는 라이브러리
import shutil                          # 파일 복사/이동 기능
import re                              # 텍스트에서 특정 패턴을 찾는 기능
import openpyxl                        # 엑셀 파일을 다루는 라이브러리
import sys                             # 시스템 정보를 가져오는 라이브러리
import pandas as pd                    # 데이터를 표 형태로 다루는 라이브러리
import json                           # JSON 파일 처리를 위한 라이브러리
import threading                       # 여러 작업을 동시에 처리하는 기능
import time                           # 시간 관련 기능
import subprocess                      # 다른 프로그램을 실행하는 기능
import socket                         # 중복 실행 방지를 위한 라이브러리
# 트레이 기능 활성화
try:
    import pystray  # type: ignore
    TRAY_AVAILABLE = True
    print("트레이 기능이 활성화되었습니다.")
    print(f"pystray 모듈: {pystray}")
except ImportError as e:
    TRAY_AVAILABLE = False
    pystray = None
    print(f"pystray 라이브러리 import 실패: {e}")
    print("트레이 기능을 사용하려면: pip install pystray pillow")
except Exception as e:
    TRAY_AVAILABLE = False
    pystray = None
    print(f"트레이 기능 초기화 중 오류: {e}")

# ============================================
# 중복 실행 방지
# ============================================

# 전역 변수로 소켓 저장
instance_socket = None

def check_single_instance():
    """중복 실행 방지 체크"""
    global instance_socket
    try:
        # 소켓을 사용하여 포트 바인딩 시도
        instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        instance_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        instance_socket.bind(('localhost', 12346))  # 포트 12346 사용
        instance_socket.listen(1)
        return True  # 성공하면 첫 번째 실행
    except socket.error:
        # 이미 바인딩된 포트가 있으면 중복 실행
        messagebox.showwarning("중복 실행", "프로그램이 이미 실행 중입니다.\n트레이 아이콘을 더블클릭하여 기존 창을 열어주세요.")
        return False

def cleanup_socket():
    """소켓 정리"""
    global instance_socket
    if instance_socket:
        try:
            instance_socket.close()
        except:
            pass

# ============================================
# 설정 저장/불러오기 함수들
# ============================================

def save_settings():
    """현재 설정을 JSON 파일에 저장"""
    try:
        # button_hotkeys에서 Button 객체를 문자열로 변환
        serializable_hotkeys = {}
        for button, hotkey in button_hotkeys.items():
            if hasattr(button, 'cget'):
                # 버튼의 텍스트를 키로 사용
                button_text = button.cget("text")
                if "(" in button_text:
                    button_text = button_text.split("(")[0].strip()
                serializable_hotkeys[button_text] = hotkey
            else:
                # 이미 문자열인 경우 그대로 사용
                serializable_hotkeys[str(button)] = hotkey
        
        settings = {
            'favorites': favorites,
            'button_hotkeys': serializable_hotkeys,
            'todo_items': todo_items,
            'last_save_time': datetime.now().isoformat()
        }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"설정 저장 완료: {len(favorites)}개 즐겨찾기, {len(serializable_hotkeys)}개 단축키")
    except Exception as e:
        print(f"설정 저장 실패: {e}")

def save_todo_settings():
    """해야할 일 설정만 별도로 저장"""
    try:
        settings = {
            'todo_items': todo_items,
            'last_save_time': datetime.now().isoformat()
        }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"해야할 일 설정 저장 완료: {len(todo_items)}개")
    except Exception as e:
        print(f"해야할 일 설정 저장 실패: {e}")

def load_settings():
    """JSON 파일에서 설정을 불러오기"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
                # 즐겨찾기 설정 불러오기
                if 'favorites' in settings:
                    # 기존 favorites 초기화 후 새로 설정
                    favorites.clear()
                    favorites.update(settings['favorites'])
                    print(f"즐겨찾기 설정 불러오기 완료: {len(settings['favorites'])}개")
                    # 각 즐겨찾기 정보 출력
                    for num, fav in favorites.items():
                        print(f"  즐겨찾기{num}: {fav.get('name', '이름 없음')}")
                
                # 단축키 설정 불러오기 (문자열 키를 Button 객체로 매핑)
                if 'button_hotkeys' in settings:
                    # 기존 button_hotkeys 초기화
                    button_hotkeys.clear()
                    
                    # 문자열 키를 실제 버튼 객체로 매핑
                    button_mapping = {
                        'RESET': reset_button,
                        'START': start_button,
                        'END': end_button
                    }
                    
                    for button_text, hotkey in settings['button_hotkeys'].items():
                        if button_text in button_mapping:
                            button_hotkeys[button_mapping[button_text]] = hotkey
                
                # 해야할 일 설정 불러오기
                if 'todo_items' in settings:
                    todo_items.clear()
                    todo_items.update(settings['todo_items'])
                    print(f"해야할 일 설정 불러오기 완료: {len(settings['todo_items'])}개")
                    
    except Exception as e:
        print(f"설정 불러오기 실패: {e}")

def apply_saved_settings():
    """저장된 설정을 UI에 적용"""
    global favorite_buttons
    
    # favorite_buttons가 정의되었는지 확인
    if 'favorite_buttons' not in globals() or not favorite_buttons:
        print("즐겨찾기 버튼이 아직 생성되지 않았습니다. 나중에 다시 시도합니다.")
        return
    
    print(f"즐겨찾기 설정 적용 시작: {len(favorites)}개 설정됨")
    print(f"현재 favorites 딕셔너리 내용: {favorites}")
    
    # 즐겨찾기 버튼 텍스트 업데이트
    for favorite_num in range(1, 9):
        # 문자열 키로 변환하여 확인
        favorite_key = str(favorite_num)
        if favorite_key in favorites:
            favorite_data = favorites[favorite_key]
            favorite_name = favorite_data.get('name', '')
            if favorite_name:
                # '_' 뒤 글자를 줄바꿈으로 표시
                if '_' in favorite_name:
                    parts = favorite_name.split('_', 1)
                    if len(parts) == 2:
                        display_text = f"{parts[0]}\n{parts[1]}"
                        favorite_buttons[favorite_num-1].config(text=display_text)
                        print(f"  즐겨찾기{favorite_num} UI 업데이트: {display_text}")
                    else:
                        favorite_buttons[favorite_num-1].config(text=favorite_name)
                        print(f"  즐겨찾기{favorite_num} UI 업데이트: {favorite_name}")
                else:
                    favorite_buttons[favorite_num-1].config(text=favorite_name)
                    print(f"  즐겨찾기{favorite_num} UI 업데이트: {favorite_name}")
                print(f"  즐겨찾기{favorite_num} 설정: {favorite_name}")
            else:
                favorite_buttons[favorite_num-1].config(text=f"즐겨찾기{favorite_num}")
                print(f"  즐겨찾기{favorite_num} 기본 텍스트로 설정")
        else:
            favorite_buttons[favorite_num-1].config(text=f"즐겨찾기{favorite_num}")
            print(f"  즐겨찾기{favorite_num} 기본 텍스트로 설정 (설정 없음)")
        
        # 강제로 UI 업데이트
        favorite_buttons[favorite_num-1].update()
    
    print(f"즐겨찾기 설정 적용 완료: {len(favorites)}개 설정됨")
    for num, fav in favorites.items():
        print(f"  즐겨찾기{num}: {fav.get('name', '이름 없음')}")
    
    # 단축키 설정 적용
    for button, hotkey in button_hotkeys.items():
        if hasattr(button, 'cget'):
            original_text = button.cget("text")
            if "(" in original_text:
                original_text = original_text.split("(")[0].strip()
            
            # 기존 버튼 폰트 설정 유지
            current_font = button.cget("font")
            if isinstance(current_font, str):
                font_parts = current_font.split()
                if len(font_parts) >= 2:
                    font_family = font_parts[0]
                    font_size = font_parts[1]
                    font_weight = font_parts[2] if len(font_parts) > 2 else "normal"
                    new_font = (font_family, font_size, font_weight)
                else:
                    new_font = current_font
            else:
                new_font = current_font
            
            button.config(text=f"{original_text} ({hotkey})", font=new_font)
            
            # 단축키 바인딩
            root.bind(f"<{hotkey}>", lambda e, btn=button: btn.invoke())

def create_tray_icon():
    """시스템 트레이 아이콘 생성"""
    if not TRAY_AVAILABLE or pystray is None:
        print("TRAY_AVAILABLE이 False이거나 pystray가 None입니다.")
        return None

    try:
        # 간단한 아이콘 생성 (파란색 원)
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 파란색 원 그리기
        draw.ellipse([8, 8, width-8, height-8], fill=(52, 152, 219), outline=(41, 128, 185), width=2)

        # 트레이 아이콘 메뉴 (default=True로 더블클릭 시 실행되도록 설정)
        menu = pystray.Menu(
            pystray.MenuItem("열기", show_window, default=True),
            pystray.MenuItem("종료", quit_application)
        )

        # 트레이 아이콘 생성
        icon = pystray.Icon("업무기록기", image, "MK 실시간 업무기록 프로그램", menu)

        print("트레이 아이콘 객체 생성 성공")
        return icon
    except Exception as e:
        print(f"트레이 아이콘 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_window(icon=None, item=None):
    """프로그램 창을 보이게 함"""
    global tray_icon

    def _show():
        global tray_icon

        # 트레이 아이콘 정리
        if icon:
            try:
                icon.stop()
            except:
                pass

        if tray_icon:
            try:
                tray_icon.stop()
            except:
                pass
            tray_icon = None

        # 창이 숨겨져 있으면 보이게 함
        if root.state() == 'withdrawn':
            root.deiconify()

        # 창을 최상위로 가져오고 포커스 설정
        root.lift()
        root.focus_force()

        # 창이 최소화되어 있으면 복원
        if root.state() == 'iconic':
            root.state('normal')

    # 메인 스레드에서 실행
    root.after(0, _show)
    
    # 창을 화면 중앙으로 이동
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

def hide_window():
    """프로그램 창을 숨기고 트레이로 이동"""
    global tray_icon
    print(f"hide_window 호출됨 - TRAY_AVAILABLE: {TRAY_AVAILABLE}, pystray: {pystray}")

    if TRAY_AVAILABLE and pystray is not None:
        try:
            print("트레이 아이콘 생성 시작...")
            # 기존 트레이 아이콘이 있으면 정리
            if tray_icon:
                try:
                    tray_icon.stop()
                except:
                    pass
                tray_icon = None

            # 창을 먼저 숨김
            root.withdraw()
            print("창 숨김 완료")

            # 새로운 트레이 아이콘 생성
            tray_icon = create_tray_icon()
            print(f"create_tray_icon 결과: {tray_icon}")

            if tray_icon:
                # 별도 스레드에서 트레이 아이콘 실행
                import threading
                tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
                tray_thread.start()
                print("트레이 스레드 시작됨")
            else:
                print("트레이 아이콘이 None입니다!")
        except Exception as e:
            print(f"트레이 아이콘 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("트레이 기능을 사용할 수 없습니다 - 창만 숨김")
        # 트레이 기능이 없으면 그냥 창만 숨김
        root.withdraw()

def end_work_and_quit():
    """업무 종료 후 프로그램 종료"""
    if start_time is not None:
        end_work()
    quit_application()

def quit_application(icon=None, item=None):
    """프로그램 완전 종료"""
    try:
        # 업무 중이면 종료
        if start_time is not None:
            end_work()
        
        # 설정 저장
        save_settings()
        
        # 트레이 아이콘 정리
        if TRAY_AVAILABLE and pystray is not None and tray_icon:
            tray_icon.stop()
        
        # 소켓 정리
        cleanup_socket()
        
        root.quit()
        root.destroy()
    except Exception as e:
        print(f"프로그램 종료 실패: {e}")
        import sys
        sys.exit(0)

def on_closing():
    """창 닫기 시 설정 저장 후 트레이로 이동"""
    # 설정 저장
    save_settings()
    hide_window()

# ============================================
# 유틸리티 함수들 (도구 함수들)
# ============================================

def extract_num(text, idx=0):
    """
    텍스트에서 숫자만 추출하는 함수
    
    매개변수:
    - text: 숫자를 찾을 텍스트
    - idx: 몇 번째 숫자를 가져올지 (0이면 첫 번째)
    
    예시:
    extract_num("ABC123DEF456", 0) → "123"
    extract_num("ABC123DEF456", 1) → "456"
    """
    if not text:  # 텍스트가 비어있으면
        return ""  # 빈 문자열 반환
    
    # 정규표현식을 사용해서 숫자만 찾기
    # \d+ 는 "하나 이상의 숫자"를 의미
    nums = re.findall(r'\d+', str(text))
    
    # 찾은 숫자들 중에서 idx번째 숫자 반환
    return nums[idx] if len(nums) > idx else ""

# ============================================
# 프로그램 경로 설정
# ============================================

# 프로그램이 실행되는 위치를 찾기
if getattr(sys, 'frozen', False):
    # 프로그램이 .exe 파일로 실행될 때
    # sys.frozen은 PyInstaller로 만든 실행파일에서만 존재
    BASE_DIR = os.path.dirname(sys.executable)  # .exe 파일이 있는 폴더
else:
    # 프로그램이 .py 파일로 실행될 때
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .py 파일이 있는 폴더

# 이미지 파일 경로를 저장할 리스트
image_paths = []

# 로그 파일의 경로 설정 (프로그램 폴더에 work_log.log 파일 생성)
LOG_FILE = os.path.join(BASE_DIR, "work_log.log")

# 설정 파일 경로
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# ============================================
# 전역 변수들 (프로그램 전체에서 사용하는 변수들)
# ============================================

start_time = None                      # 업무 시작 시간을 저장
last_end_time = None                   # 마지막 업무 종료 시간을 저장
log_filter_mode = "today"              # 로그 필터 모드 ("today" 또는 "all")
favorites = {}                        # 즐겨찾기 정보를 저장하는 딕셔너리
button_hotkeys = {}                   # 버튼별 단축키를 저장하는 딕셔너리
work_status_animation_id = None        # 업무 상태 애니메이션을 제어하는 ID
tray_icon = None                      # 시스템 트레이 아이콘
todo_items = {}                       # 해야할 일 정보를 저장하는 딕셔너리

# 프로그램 시작 시 설정 로딩 (UI 생성 전에 수행)
print("프로그램 시작 - 설정 로딩 중...")

# 최초 실행 여부 확인 (settings.json 파일이 없으면 최초 실행)
if not os.path.exists(SETTINGS_FILE):
    print("최초 실행 - 설정 초기화")
    favorites.clear()
    button_hotkeys.clear()
    todo_items.clear()
    print("설정 초기화 완료")
else:
    print("기존 설정 파일 발견 - 설정 유지")

# 설정 로딩 (성능 최적화를 위해 지연 로딩)
def load_settings_later():
    load_settings()
    print("설정 로딩 완료")

# 해야할 일 테이블 초기화 함수
def init_todo_table():
    update_todo_table()

# 정렬 관련 변수들
sort_column = "날짜"                   # 현재 정렬 기준 컬럼
sort_reverse = False                   # 정렬 순서 (False=오름차순, True=내림차순)

# 각 컬럼별 정렬 상태를 독립적으로 관리하는 딕셔너리
column_sort_states = {
    "날짜": False,      # 날짜 컬럼 정렬 상태
    "시작시간": False,  # 시작시간 컬럼 정렬 상태
    "완료시간": False,  # 완료시간 컬럼 정렬 상태
    "코드": False,      # 코드 컬럼 정렬 상태
    "MK번호": False,    # MK번호 컬럼 정렬 상태
    "공정명": False,    # 공정명 컬럼 정렬 상태
    "업무내용": False,  # 업무내용 컬럼 정렬 상태
    "소요시간": False   # 소요시간 컬럼 정렬 상태
}

# ============================================
# 정렬 관련 함수들
# ============================================

def sort_treeview(col):
    """
    트리뷰(표)를 지정된 컬럼으로 정렬하는 함수
    
    매개변수:
    - col: 정렬할 컬럼 이름
    """
    global sort_column, sort_reverse, column_sort_states
    
    # tree 객체가 아직 정의되지 않았으면 함수 종료
    if 'tree' not in globals():
        return
    
    # 날짜 컬럼만 정렬 가능하도록 제한
    if col != "날짜":
        return
    
    # 해당 컬럼의 정렬 상태를 독립적으로 관리
    if sort_column == col:
        # 같은 컬럼을 다시 클릭하면 정렬 순서를 바꿈
        column_sort_states[col] = not column_sort_states[col]
        sort_reverse = column_sort_states[col]
    else:
        # 다른 컬럼을 클릭하면 해당 컬럼으로 정렬
        sort_column = col
        column_sort_states[col] = False
        sort_reverse = False
    
    # 모든 항목을 가져와서 정렬
    items = [(tree.set(item, col), item) for item in tree.get_children('')]
    
    # 날짜 컬럼만 정렬
    if col == "날짜":
        items.sort(key=lambda x: x[0], reverse=sort_reverse)
    
    # 정렬된 순서로 다시 삽입
    for index, (val, item) in enumerate(items):
        tree.move(item, '', index)
    
    # 헤더에 정렬 표시 업데이트
    update_sort_headers(col)

def update_sort_headers(active_col):
    """헤더에 정렬 표시 업데이트"""
    # tree 객체가 아직 정의되지 않았으면 무시
    if 'tree' not in globals():
        return
        
    columns = ["날짜", "시작시간", "완료시간", "코드", "MK번호", "공정명", "업무 내용", "소요시간"]
    for col in columns:
        if col == active_col and col == "날짜":
            arrow = " ▼" if column_sort_states.get(col, False) else " ▲"
            tree.heading(col, text=f"{col}{arrow}")
        else:
            tree.heading(col, text=col)

# 버튼 텍스트
button_texts = {
    "설계": "설계대응", "수정": "수정대응", "검토": "검토대응", "전화": "전화대응", "호출": "호출대응",
    "발주": "발주대응", "현장": "현장대응", "문서": "문서대응", "DR회의": "DR회의",
    "설계회의": "설계회의", "일반회의": "일반회의", "교육회의": "교육회의", "외출": "외출", "개인업무": "개인업무"
}

# 카테고리 목록 (작업코드별 공정명)
category_list = [
    # CAD 작업코드별 공정명
    "선행검토", "구조 설계", "구조 DR", "내부 DR", "금형 DR", "M/B 발주", 
    "건드릴/황삭 DATA", "3D 설계", "수정 데이터 반영", "해석데이터 발송", 
    "2D 설계", "자재표", "자료발주", "도면출도",
    
    # KT 작업코드별 공정명
    "금형 기본자료 작성", "제품 검토서 작성", "수정 데이터 점검/검토", 
    "설계 검토 및 지원", "현장대응", "시사출 보고서 작성", 
    "설계 외주관리", "설계 데이터 발송", "팩터 DATA 발송", "승인원 작성", 
    "인자표 작성", "PSR 작성", "스페어리스트 견적/승인/발주", 
    "코팅리스트 견적/승인/발주", "출장업무(공무관련, 이동시간)", 
    "사출지원", "기타서류 업무",
    
    # ET 작업코드별 공정명
    "TO 이후 수정", "제품 데이터 수정 검토", "수정검토서 작성", 
    "설계변경 도면작성 및 출도",
    
    # KC 작업코드별 공정명
    "수주 전 견적기초도면 작성", "수주 전 제품데이터 검토", "일반회의", 
    "교육(업무관련)", "표준화 작업", "심사관련 업무", "기타서류 업무",
    
    # TT 작업코드별 공정명
    "교육(업무무관)", "개인업무능력 STUDY", "외출", "청소", "무(일 없는 경우)"
]

# 공정명과 작업코드 매핑 관계
category_code_mapping = {
    # CAD 작업코드별 공정명
    "선행검토": "CAD", "구조 설계": "CAD", "구조 DR": "CAD", "내부 DR": "CAD", 
    "금형 DR": "CAD", "M/B 발주": "CAD", "건드릴/황삭 DATA": "CAD", 
    "3D 설계": "CAD", "수정 데이터터 반영": "CAD", "해석데이터 발송": "CAD", 
    "2D 설계": "CAD", "자재표": "CAD", "자료발주": "CAD", "도면출도": "CAD",
    
    # KT 작업코드별 공정명
    "금형 기본자료 작성": "KT", "제품 검토서 작성": "KT", "수정 데이터 점검/검토": "KT", 
    "설계 검토 및 지원": "KT", "현장대응": "KT", "시사출 보고서 작성": "KT", 
    "설계 외주관리": "KT", "설계 데이터 발송": "KT", "팩터 DATA 발송": "KT", 
    "승인원 작성": "KT", "인자표 작성": "KT", "PSR 작성": "KT", 
    "스페어리스트 견적/승인/발주": "KT", "코팅리스트 견적/승인/발주": "KT", 
    "출장업무(공무관련, 이동시간)": "KT", "사출지원": "KT", "기타서류 업무": "KT",
    
    # ET 작업코드별 공정명
    "TO 이후 수정": "ET", "제품 데이터 수정 검토": "ET", "수정검토서 작성": "ET", 
    "설계변경 도면작성 및 출도": "ET",
    
    # KC 작업코드별 공정명
    "수주 전 견적기초도면 작성": "KC", "수주 전 제품데이터 검토": "KC", "일반회의": "KC", 
    "교육(업무관련)": "KC", "표준화 작업": "KC", "심사관련 업무": "KC", "기타서류 업무": "KC",
    
    # TT 작업코드별 공정명
    "교육(업무무관)": "TT", "개인업무능력 STUDY": "TT", "외출": "TT", "청소": "TT", 
    "무(일 없는 경우)": "TT"
}

# ============================================
# 공정명 관련 함수들
# ============================================

def update_code_from_category(event=None):
    """
    공정명을 선택했을 때 자동으로 작업코드를 변경하는 함수
    
    매개변수:
    - event: 이벤트 정보 (콤보박스에서 선택할 때 자동으로 전달됨)
    
    동작:
    1. 선택된 공정명을 가져옴
    2. 공정명에 맞는 작업코드를 찾음
    3. 작업코드 입력창에 자동으로 설정
    """
    selected_category = category_entry.get().strip()  # 선택된 공정명 가져오기
    
    # 공정명에 맞는 작업코드가 있으면 자동 설정
    if selected_category in category_code_mapping:
        code_entry.set(category_code_mapping[selected_category])

# ============================================
# 애니메이션 관련 함수들
# ============================================

def animate_work_status():
    """
    업무 중일 때 상태 표시를 애니메이션으로 보여주는 함수
    
    동작:
    1. 업무 중일 때만 애니메이션 실행
    2. "업무ing..." ↔ "업무ing" 텍스트를 0.5초마다 바꿈
    3. 깜빡이는 효과로 업무 중임을 시각적으로 표시
    """
    global work_status_animation_id
    
    # 업무 중일 때만 애니메이션 실행
    if start_time is not None:
        current_text = status_label.cget("text")  # 현재 표시된 텍스트 가져오기
        
        # 텍스트를 번갈아가며 표시 (깜빡이는 효과)
        if current_text == "업무ing...":
            status_label.config(text="업무ing")
        else:
            status_label.config(text="업무ing...")
        
        # 0.5초 후에 다시 이 함수를 호출 (재귀적 애니메이션)
        work_status_animation_id = root.after(500, animate_work_status)

# 작업분류 아래 버튼들 배치
button_list = list(button_texts.keys())

# ============================================
# 로그 및 초기화 관련 함수들
# ============================================

def log_to_file(message):
    """
    메시지를 로그 파일에 기록하는 함수
    
    매개변수:
    - message: 기록할 메시지
    
    동작:
    1. 로그 파일이 있는 폴더를 생성 (없으면)
    2. 메시지를 파일 끝에 추가
    3. 오류 발생 시 사용자에게 알림
    """
    try:
        # 로그 파일이 있는 폴더를 생성 (없으면 생성)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # 파일을 열어서 메시지를 끝에 추가 (append 모드)
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(message + "\n")
    except Exception as e:
        # 오류 발생 시 사용자에게 알림
        messagebox.showerror("오류", f"로그 파일에 쓰기 실패: {e}")

def reset_work():
    """
    모든 업무 관련 정보를 초기화하는 함수
    
    동작:
    1. 업무 시작 시간을 None으로 설정
    2. 모든 입력창을 비움
    3. 상태를 "업무 대기"로 변경
    4. 타이머와 애니메이션을 정지
    """
    global start_time
    
    # 업무 시작 시간을 None으로 설정하여 완전히 RESET 상태로 만듦
    start_time = None
    
    # UI 초기화 (모든 입력창 비우기)
    category_entry.set("")           # 공정명 입력창 비우기
    code_entry.set("")               # 작업코드 입력창 비우기
    mk_entry.delete(0, tk.END)       # MK번호 입력창 비우기
    task_entry.delete("1.0", tk.END) # 업무내용 입력창 비우기
    task_entry.config(state="normal") # 업무내용 입력창 활성화
    
    # 상태를 "업무 대기"로 설정
    status_label.config(text="업무 대기")
    
    # 타이머 정지
    stop_work_timer()
    
    # 업무 상태 애니메이션 중지
    global work_status_animation_id
    if work_status_animation_id:
        root.after_cancel(work_status_animation_id)  # 예약된 애니메이션 취소
        work_status_animation_id = None

# ============================================
# 클립보드 관련 함수들
# ============================================

def paste_from_clipboard(event=None):
    """
    클립보드의 내용을 업무내용 입력창에 붙여넣는 함수
    
    매개변수:
    - event: 이벤트 정보 (Ctrl+V 단축키 사용 시 자동으로 전달됨)
    
    동작:
    1. 클립보드에서 텍스트를 가져옴
    2. 업무내용 입력창에 붙여넣기
    3. 오류 발생 시 콘솔에 출력
    """
    try:
        # 클립보드에서 텍스트 가져오기
        text = pyperclip.paste()
        
        # 텍스트가 있으면 업무내용 입력창에 붙여넣기
        if text:
            task_entry.insert(tk.END, text + "\n")
    except Exception as e:
        # 오류 발생 시 콘솔에 출력 (사용자에게는 표시하지 않음)
        print(f"붙여넣기 오류: {e}")

# 업무 시작 묻기 - 팝업으로 대체됨

# ============================================
# 업무 시작/종료 관련 함수들
# ============================================

def start_work():
    """
    업무를 시작하는 함수
    
    동작:
    1. 이미 업무 중이면 사용자에게 확인
    2. 입력 정보 검증 (작업코드, MK번호, 공정명)
    3. 업무 시작 시간 기록
    4. 타이머와 애니메이션 시작
    5. 상태 표시 변경
    """
    global start_time
    auto_end_mode = False  # 자동 종료 모드 플래그
    
    # 이미 업무 중인지 확인
    if start_time is not None:
        # 사용자에게 새로운 업무 시작 여부 확인
        if messagebox.askyesno("확인", "이미 작업이 진행 중입니다. 새로운 작업을 시작하시겠습니까?"):
            # 기존 작업을 종료하고 로그에 저장
            end_work(auto_end=True)
            # 완전히 RESET 상태로 초기화
            reset_work()
            auto_end_mode = True
        else:
            return  # 사용자가 취소하면 함수 종료
    
    # auto_end 모드일 때는 새로운 업무를 시작하지 않음
    if auto_end_mode:
        return
    
    # 입력된 정보들 가져오기
    mk_number = convert_mk_to_uppercase(mk_entry.get().strip())    # MK번호 (대문자 변환)
    category = category_entry.get().strip()  # 공정명
    code = code_entry.get().strip()       # 작업코드
    
    # 작업코드 검증 (반드시 입력되어야 함)
    if not code:
        messagebox.showerror("오류", "작업코드를 선택해주세요.")
        return
    
    # KC/TT 작업코드는 MK번호가 필수가 아님 (MK번호 없어도 실행 가능)
    if code in ["KC", "TT"]:
        if not category:
            messagebox.showerror("오류", "공정명을 입력해주세요.")
            return
    else:
        # CAD/ET/KT 작업코드는 MK번호 필수
        if not mk_number:
            messagebox.showerror("오류", "MK번호를 입력해주세요.")
            return
        
        # MK번호 형식 검증
        is_valid, error_message = validate_mk_number(mk_number)
        if not is_valid:
            messagebox.showerror("오류", error_message)
            return
        
        if not category:
            messagebox.showerror("오류", "공정명을 입력해주세요.")
            return

    start_time = datetime.now()
    status_label.config(text="업무ing...")
    start_work_timer()
    
    # 작성 내용 커서 제거
    task_entry.config(state="disabled")
    
    # 업무 상태 애니메이션 시작
    animate_work_status()
    
    # 로그 파일에 업무 시작 기록
    start_message = f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] 업무 시작"
    log_to_file(start_message)
    
    # 버튼 텍스트에 단축키 표시 유지
    current_text = start_button.cget("text")
    if "(" in current_text:
        hotkey_part = current_text[current_text.find("("):]
        start_button.config(text=f"START {hotkey_part}")

# 공지사항 창 함수
def show_notice():
    notice_window = tk.Toplevel(root)
    notice_window.title("공지사항")
    notice_window.geometry("600x400")
    notice_window.resizable(True, True)
    notice_window.transient(root)
    notice_window.grab_set()
    
    # ESC 키로 창 닫기
    def on_escape(event):
        notice_window.destroy()
    
    notice_window.bind("<Escape>", on_escape)
    
    # 창에 포커스 설정
    notice_window.focus_set()
    
    # 스크롤 가능한 텍스트 위젯
    text_frame = tk.Frame(notice_window)
    text_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    notice_text = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Arial", 11))
    notice_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=notice_text.yview)
    
    # 공지사항 내용
    notice_content = """
[업데이트 로그]

버전 1.1 (2025-10-04) - 로그 편집 기능 개선
====================================================

🎯 주요 개선사항
• 로그 더블클릭으로 즉시 편집 가능
• 해야할 업무 관리 시스템 완전 구현
• 중요 표시 기능으로 우선순위 관리
• 트레이 아이콘 기능 안정화
• UI/UX 전면 개선

📋 해야할 업무 기능 (NEW!)
• 등록/편집/삭제 완전 지원
• MK번호 + 공정명 + 업무내용 조합 표시
• 기한 설정 및 D-day 자동 계산
• 중요 표시로 최상단 고정 배치
• 우클릭 메뉴로 편집/삭제/중요 표시
• 다중선택 후 Delete 키로 일괄 삭제

⭐ 중요 표시 시스템 (NEW!)
• ✅ 아이콘으로 중요 업무 표시
• 중요 업무는 무조건 리스트 최상단 배치
• 우클릭 메뉴에서 "중요 표시/해제" 선택
• 시각적 구분으로 업무 우선순위 관리

🖥️ 트레이 아이콘 기능 개선
• 더블클릭으로만 프로그램 창 열기 (오작동 방지)
• 0.5초 이내 더블클릭 감지 로직
• 우클릭 메뉴: 열기/종료 선택
• 시스템 트레이에서 백그라운드 실행

🎨 UI/UX 개선
• 해야할 업무 등록/편집 창 통일된 디자인
• 창 크기 최적화로 깔끔한 인터페이스
• 버튼 배치 및 여백 최적화
• 전체적인 디자인 통일성 향상

🔧 기술적 개선
• 날짜선택 중복 방지 기능
• 공정명-작업구분 자동 연계
• 오류 처리 강화
• 메모리 사용량 최적화

버전 2.0 (2025-08-07)
====================================================

📊 엑셀 내보내기 완전 개선
• 파일명 자동 설정: 업무기록(ALL/TODAY)_YYMMDD.xlsx
• 열 너비 최적화 및 정렬 개선
• 필터 기능 자동 적용
• 누적시간 컬럼 추가
• 소요시간 분 단위 정수 표시
• 엑셀 파일 자동 열기

⚡ 단축키 시스템
• 버튼 우클릭으로 단축키 설정
• 초기화 버튼으로 단축키 완전 제거
• ESC 키로 창 닫기
• 설정창 크기 최적화

💾 즐겨찾기 기능
• 8개 즐겨찾기 버튼 지원
• MK번호, 공정명, 작업구분, 작업내용 저장
• 초기화 버튼으로 설정 완전 제거
• 버튼 클릭 시 자동 입력

🎯 실시간 업무 관리
• 실시간 작업 소요시간 표시
• 업무 상태 애니메이션
• 자동 로그 기록
• 중복 실행 방지

[상세 사용법]

1. 📝 업무 시작하기
   =================
   • MK번호 입력 (CAD/ET/KT 작업코드의 경우)
     - 숫자 5자리 + M/T/R (예: 25001M)
     - M/T/R 버튼으로 자동 대문자 변환
   • 공정명 선택 (콤보박스)
     - 선택 시 작업구분 자동 변경
   • START 버튼 클릭
   • 실시간 소요시간 표시 시작

2. ⏹️ 업무 종료하기
   =================
   • END 버튼 클릭
   • 자동으로 로그에 기록
   • 소요시간 자동 계산
   • 입력 필드 자동 초기화

3. 📋 해야할 업무 관리
   ================================
   • 등록: "등록" 버튼 클릭 → 해야할 업무 등록 창
   • 편집: 항목 더블클릭 또는 우클릭 → "편집"
   • 삭제: 우클릭 → "삭제" 또는 Delete 키
   • 중요 표시: 우클릭 → "중요 표시/해제"
   • 기한 설정: 날짜선택 버튼으로 캘린더에서 선택
   • D-day 자동 계산 및 표시

4. 📊 로그 관리
   =============
   • 로그 더블클릭: 편집 창 열기
   • 로그 추가: "로그 추가" 버튼
   • 로그 삭제: 우클릭 → "삭제"
   • 필터링: "전체 기록보기" ↔ "오늘 기록보기"
   • 정렬: 헤더 클릭으로 날짜 기준 정렬

5. 📈 엑셀 내보내기
   =================
   • "엑셀로 내보내기" 버튼 클릭
   • 파일명 자동 설정
   • 열 너비 최적화
   • 필터 기능 자동 적용
   • 누적시간 컬럼 포함
   • 엑셀 파일 자동 열기

6. ⭐ 즐겨찾기 기능
   =================
   • 즐겨찾기 버튼 우클릭: 설정 창
   • MK번호, 공정명, 작업구분, 작업내용 저장
   • 초기화 버튼: 모든 설정 내용 빈칸으로 초기화
   • 버튼 클릭 시 자동 입력

7. ⌨️ 단축키 설정
   ===============
   • 버튼 우클릭: 단축키 설정 창
   • 원하는 키 조합 입력
   • 초기화 버튼: 단축키 완전 제거
   • ESC 키: 창 닫기

8. 🖥️ 트레이 아이콘 기능
   =====================
   • 창 닫기 시 트레이로 이동
   • 더블클릭: 프로그램 창 열기
   • 우클릭: 메뉴 (열기/종료)
   • 백그라운드에서 실행

[작업코드별 MK번호 요구사항]
==========================
• CAD/ET/KT: MK번호 필수 (예: 25001M, 25002T, 25003R)
• KC/TT: MK번호 불필요 (개인업무, 교육 등)

[엑셀 내보내기 특징]
===================
• 전체 기록: 업무기록(ALL)_YYMMDD.xlsx
• 오늘 기록: 업무기록(TODAY)_YYMMDD.xlsx
• 모든 컬럼에 필터 적용
• 헤더 가운데 정렬, 굵은 글씨
• 데이터 정렬: 날짜/시간/코드/MK번호/시간은 가운데, 공정명/내용은 왼쪽
• 누적시간 컬럼으로 총 작업시간 확인

[해야할 업무 관리 팁]
===================
• 중요 업무는 ✅ 표시로 최상단 고정
• 기한이 지난 업무는 D+로 표시
• 오늘 마감 업무는 D-day로 표시
• 앞으로 남은 업무는 D-로 표시
• 우클릭 메뉴로 빠른 편집/삭제
• 다중선택 후 Delete 키로 일괄 삭제

[문의사항]
==========
개발자에게 개선사항이나 버그를 보고하시면 
다음 업데이트에 반영하겠습니다.
    """
    
    notice_text.insert("1.0", notice_content)
    notice_text.config(state="disabled")  # 읽기 전용
    
    # 닫기 버튼
    close_button = tk.Button(notice_window, text="닫기", command=notice_window.destroy, 
                            bg="#4caf50", fg="white", width=10)
    close_button.pack(pady=10)

# 코드 자동 생성 함수
def generate_code(category, mk_number):
    # 새로운 공정명에 맞는 코드 생성
    if category in category_code_mapping:
        return category_code_mapping[category]
    return ""

# 콤보박스 선택 시 코드 자동 업데이트
def update_code(event):
    selected_category = category_entry.get()
    mk_number = mk_entry.get().strip()
    generated_code = generate_code(selected_category, mk_number)
    code_entry.set(generated_code if generated_code else "")

# 업무 종료 함수
def end_work(auto_end=False):
    global start_time
    if start_time is None:
        return

    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_minutes = int(elapsed.total_seconds() // 60)
    
    # 소요시간을 "0시간 0분 00초" 형식으로 변환
    hours = elapsed_minutes // 60
    minutes = elapsed_minutes % 60
    seconds = int(elapsed.total_seconds() % 60)
    duration_str = f"{hours}시간 {minutes}분 {seconds:02d}초"
    
    # 로그 파일에 기록
    log_message = (
        f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] 업무 종료 - "
        f"코드: {code_entry.get()}, "
        f"MK번호: {convert_mk_to_uppercase(mk_entry.get())}, "
        f"작업분류: {category_entry.get()}, "
        f"작업: {task_entry.get('1.0', tk.END).strip()} "
        f"(소요 시간: {hours}시간 {minutes}분 {seconds}초)"
    )
    log_to_file(log_message)

    # 로그에 기록 (시작/완료시간 띄어쓰기 수정)
    log_entry = (
        start_time.strftime("%Y-%m-%d"),
        start_time.strftime("%H시 %M분"),
        end_time.strftime("%H시 %M분"),
        code_entry.get(),
        convert_mk_to_uppercase(mk_entry.get()),  # MK번호 대문자 변환
        category_entry.get(),
        task_entry.get("1.0", tk.END).strip(),
        duration_str
    )
    tree.insert("", "end", values=log_entry)
    
    # UI 초기화 (업무 종료 시 항상 초기화)
    mk_entry.delete(0, tk.END)
    category_entry.set("")
    
    # 업무 내용 입력창 강제 초기화
    try:
        task_entry.config(state="normal")  # 먼저 활성화
        task_entry.delete("1.0", tk.END)  # 내용 삭제
        task_entry.insert("1.0", "")      # 빈 문자열로 확실히 초기화
        
        # 추가로 한 번 더 초기화 (다른 함수에서 다시 설정될 수 있으므로)
        root.after(100, lambda: task_entry.delete("1.0", tk.END))
        root.after(200, lambda: task_entry.delete("1.0", tk.END))
    except Exception as e:
        # 대안 방법: 위젯을 다시 생성
        task_entry.config(state="normal")
        task_entry.delete("1.0", tk.END)
    
    code_entry.set("")
    
    start_time = None
    status_label.config(text="업무 대기")
    stop_work_timer()
    
    # 업무 상태 애니메이션 중지
    global work_status_animation_id
    if work_status_animation_id:
        root.after_cancel(work_status_animation_id)
        work_status_animation_id = None
    
    # 버튼 텍스트에 단축키 표시 유지
    current_text = start_button.cget("text")
    if "(" in current_text:
        hotkey_part = current_text[current_text.find("("):]
        start_button.config(text=f"START {hotkey_part}")

# 로그 기록 불러오기 함수
def load_logs():
    try:
        # 기존 항목 삭제
        for item in tree.get_children():
            tree.delete(item)
        
        # 로그 파일 읽기
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        # 로그 데이터 파싱
        logs = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 업무 시작 로그 패턴 확인
            start_pattern = re.compile(
                r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 업무 시작"
            )
            
            start_match = start_pattern.search(line)
            if start_match:
                start_timestamp = start_match.group(1)
                start_date = start_timestamp[:10]
                start_time = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H시 %M분")
                
                # 다음 줄에서 업무 종료 로그 찾기
                if i + 1 < len(lines):
                    end_line = lines[i + 1].strip()
                    
                    # 업무 종료 로그인지 확인
                    if "업무 종료" in end_line:
                        # 정규표현식으로 파싱 시도
                        end_pattern = re.compile(
                            r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 업무 종료 - 코드: ([^,]*?)(?:, MK번호: ([^,]*))?(?:, 작업분류: ([^,]*))?(?:, 작업: ([^,]*))? \(소요 시간: (\d+)시간 (\d+)분 (\d+)초\)"
                        )
                        
                        end_match = end_pattern.search(end_line)
                        if end_match:
                            end_timestamp = end_match.group(1)
                            end_time = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H시 %M분")
                            code = end_match.group(2).strip()
                            mk_number = (end_match.group(3) or "").strip()
                            category = (end_match.group(4) or "").strip()
                            task = (end_match.group(5) or "").strip()
                            hours = end_match.group(6)
                            minutes = end_match.group(7)
                            seconds = end_match.group(8)
                            duration = f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초"
                            
                            # 로그 데이터 추가
                            logs.append({
                                'date': start_date,
                                'start_time': start_time,
                                'end_time': end_time,
                                'code': code,
                                'mk_number': mk_number,
                                'category': category,
                                'task': task,
                                'duration': duration,
                                'timestamp': end_timestamp
                            })
                
                i += 2  # 시작과 종료 로그를 건너뛰기
            else:
                i += 1
        
        # 필터 모드에 따라 로그 표시
        today = datetime.now().strftime("%Y-%m-%d")
        if log_filter_mode == "today":
            filtered_logs = [log for log in logs if log['date'] == today]
        else:
            filtered_logs = logs
        
        # Treeview에 로그 추가
        for log in filtered_logs:
            tree.insert("", "end", values=(
                log['date'],
                log['start_time'],
                log['end_time'],
                log['code'],
                log['mk_number'],
                log['category'],
                log['task'],
                log['duration']
            ))
        
        # 날짜 기준으로 정렬 (기본값)
        sort_by_date()
        
    except FileNotFoundError:
        # 로그 파일이 없으면 조용히 넘어감 (새로 시작하는 경우)
        pass
    except Exception as e:
        messagebox.showerror("오류", f"로그 파일 처리 실패: {str(e)}")

# 시작시간 기준 정렬 함수
def sort_by_start_time():
    items = [(tree.set(item, "시작시간"), item) for item in tree.get_children("")]
    items.sort(key=lambda x: x[0])
    
    for index, (val, item) in enumerate(items):
        tree.move(item, "", index)

# 날짜 기준 정렬 함수 (기본값)
def sort_by_date():
    items = [(tree.set(item, "날짜"), item) for item in tree.get_children("")]
    items.sort(key=lambda x: x[0])
    
    for index, (val, item) in enumerate(items):
        tree.move(item, "", index)

# 전체/오늘 로그 전환 함수 추가
def toggle_log_filter():
    global log_filter_mode
    if log_filter_mode == "today":
        log_filter_mode = "all"
        reload_log_button.config(text="오늘 기록보기")
    else:
        log_filter_mode = "today"
        reload_log_button.config(text="전체 기록보기")
    load_logs()  # 로그 다시 불러오기

# 로그파일 열기 함수
def open_log_file():
    if os.path.exists(LOG_FILE):
        try:
            if sys.platform.startswith('win'):
                os.startfile(LOG_FILE)
            elif sys.platform == 'darwin':
                subprocess.call(['open', LOG_FILE])
            else:
                subprocess.call(['xdg-open', LOG_FILE])
        except Exception as e:
            messagebox.showerror("오류", f"로그 파일 열기 실패: {e}")
    else:
        messagebox.showinfo("알림", "로그 파일이 존재하지 않습니다.")

# 엑셀 파일로 내보내기 함수
def time_to_minutes(time_str):
    # 공백을 제거하여 일관된 처리
    time_str = time_str.replace(" ", "")

    # 정규표현식으로 시간, 분, 초 추출
    match = re.match(r'(?:(\d+)시간)?(?:(\d+)분)?(?:(\d+)초)?', time_str)
    if not match:
        return 0
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    # 시간, 분, 초를 모두 분으로 환산
    total_minutes = (hours * 60) + minutes + (seconds / 60)
    
    # 결과를 소수점까지 포함하여 반환 (혹은 int로 반올림/버림 가능)
    return total_minutes


def export_to_excel_with_macro():
    """엑셀 파일로 내보내기 (개선된 버전)"""
    
    try:
        import pandas as pd
        from openpyxl import load_workbook
        from openpyxl.styles import Alignment, Font
        from openpyxl.utils import get_column_letter
    except ImportError as e:
        messagebox.showerror("오류", f"필요한 라이브러리가 설치되어 있지 않습니다: {e}\n\n다음 명령어로 설치해주세요:\npip install pandas openpyxl")
        return

    # 파일명 설정 (전체/오늘 기록에 따라)
    if log_filter_mode == "today":
        default_filename = f"금일 업무기록_{datetime.now().strftime('%Y%m%d')}.xlsx"
    else:
        default_filename = f"전체 업무기록_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Workbook", "*.xlsx")],
        initialfile=default_filename
    )
    
    if not file_path:
        return
    
    try:
        # 데이터 수집
        columns = tree["columns"]
        data = []
        
        for item in tree.get_children():
            values = tree.item(item, 'values')
            if values:
                data.append(list(values))
        
        if not data:
            messagebox.showwarning("경고", "내보낼 데이터가 없습니다.")
            return
        
        # DataFrame 생성
        df = pd.DataFrame(data, columns=columns)
        
        # 소요시간을 분 단위로 변환
        def convert_to_minutes(time_str):
            if not time_str:
                return 0
            try:
                # "X시간 Y분 Z초" 형식을 분으로 변환
                time_str = str(time_str).strip()
                hours = minutes = seconds = 0
                
                if '시간' in time_str:
                    hours = int(time_str.split('시간')[0])
                    time_str = time_str.split('시간')[1]
                if '분' in time_str:
                    minutes = int(time_str.split('분')[0])
                    time_str = time_str.split('분')[1]
                if '초' in time_str:
                    seconds = int(time_str.split('초')[0])
                
                total_minutes = hours * 60 + minutes + seconds / 60
                return int(round(total_minutes))  # 정수로 변환
            except:
                return 0
        
        # 소요시간 컬럼을 분 단위로 변환
        if '소요시간' in df.columns:
            df['소요시간(분)'] = df['소요시간'].apply(convert_to_minutes)
            df = df.drop('소요시간', axis=1)
        
        # 누적시간 계산
        df['누적시간(분)'] = df['소요시간(분)'].cumsum()
        
        # 엑셀 파일로 저장
        df.to_excel(file_path, index=False, sheet_name='업무기록')
        
        # 엑셀 파일 스타일링
        wb = load_workbook(file_path)
        ws = wb['업무기록']
        
        # 열 너비 설정 (고정값)
        column_widths = {
            'A': 15,  # 날짜
            'B': 15,  # 시작시간
            'C': 15,  # 완료시간
            'D': 10,  # 코드
            'E': 15,  # MK번호
            'F': 30,  # 공정명
            'G': 30,  # 업무내용
            'H': 15,  # 소요시간(분)
            'I': 15   # 누적시간(분)
        }
        
        for column_letter, width in column_widths.items():
            ws.column_dimensions[column_letter].width = width
        
        # 헤더 스타일링 (가운데 정렬, 굵은 글씨)
        header_font = Font(bold=True)
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = header_alignment
        
        # 데이터 셀 스타일링
        for row in ws.iter_rows(min_row=2):
            for i, cell in enumerate(row):
                if i in [0, 1, 2, 3, 4, 7, 8]:  # 날짜, 시작시간, 완료시간, 코드, MK번호, 소요시간, 누적시간
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                else:  # 공정명, 업무내용
                    cell.alignment = Alignment(horizontal='left', vertical='center')
        
        # 필터 추가
        ws.auto_filter.ref = ws.dimensions
        
        # 파일 저장
        wb.save(file_path)
        
        # 엑셀 파일 열기
        if os.path.exists(file_path):
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', file_path])
            else:
                subprocess.call(['xdg-open', file_path])

    except PermissionError as e:
        messagebox.showerror("권한 오류", 
                           "파일이 다른 프로그램에서 사용 중입니다.\n"
                           "다른 이름으로 저장하거나 파일을 닫은 후 다시 시도해주세요.")
    except Exception as e:
        messagebox.showerror("오류", f"엑셀 내보내기 실패: {e}")
        print(f"엑셀 내보내기 오류: {e}")
        import traceback
        traceback.print_exc()

# VBA 매크로 함수 제거 (복잡성으로 인한 오류 방지)













# 카테고리 버튼을 눌렀을 때 자동으로 콤보박스에 값을 입력하도록 설정
def set_category(category):
    category_entry.set(button_texts.get(category, category))
    update_code(None) # 카테고리 선택 시 코드 업데이트

# 버튼 이름 변경 함수
def change_button_name(button, button_type):
    new_name = simpledialog.askstring("버튼 이름 변경", "새로운 버튼 이름을 입력하세요:")
    if new_name:
        button_text = button["text"]
        button.config(text=new_name)
        for key, value in button_texts.items():
            if value == button_text:
                button_texts[key] = new_name
                break

# 버튼 생성 함수
def create_button(frame, text, command, button_type, width=4, bg="#cad5ee", height=1):
    button = tk.Button(frame, text=text, command=command, width=width, bg=bg, height=height)
    button.bind("<Button-3>", lambda event: show_context_menu(event, button, button_type))
    return button

# 컨텍스트 메뉴 표시 함수
def show_context_menu(event, button, button_type):
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="이름 변경", command=lambda: change_button_name(button, button_type))
    context_menu.tk_popup(event.x_root, event.y_root)

# 즐겨찾기 설정 창
class FavoriteSettingDialog:
    def __init__(self, parent, favorite_num):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"즐겨찾기{favorite_num} 설정")
        self.dialog.geometry("350x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.favorite_num = favorite_num
        self.result = None
        
        # 즐겨찾기 데이터 (기존 데이터 불러오기)
        favorite_key = str(favorite_num)
        self.favorite_data = favorites.get(favorite_key, {
            "name": f"즐겨찾기{favorite_num}",
            "mk_number": "",
            "category": "",
            "code": "",
            "task": ""
        })
        
        self.create_widgets()
        self.center_window()
        
    def create_widgets(self):
        # ESC 키로 창 닫기 바인딩
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
        
        # 창에 포커스 설정
        self.dialog.focus_set()
        
        # 즐겨찾기명
        tk.Label(self.dialog, text="즐겨찾기명:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.name_entry = tk.Entry(self.dialog, width=15, font=("Arial", 12))
        self.name_entry.insert(0, self.favorite_data["name"])
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # 글자수 제한 기능
        def limit_name_length(new_value):
            try:
                if len(new_value) > 15:
                    return False  # 15글자 초과면 입력 차단
                return True
            except:
                return True  # 오류 발생 시 입력 허용
        
        self.name_entry.config(validate="key", validatecommand=(self.dialog.register(limit_name_length), "%P"))
        
        # MK번호
        tk.Label(self.dialog, text="MK번호:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        # MK번호 입력 프레임
        mk_frame = tk.Frame(self.dialog)
        mk_frame.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.mk_entry = tk.Entry(mk_frame, width=15, font=("Arial", 12))
        self.mk_entry.insert(0, self.favorite_data["mk_number"])
        self.mk_entry.pack(side=tk.LEFT)
        
        # MK번호 입력 시 대문자 변환
        def on_mk_entry_change_dialog(*args):
            current = self.mk_entry.get()
            if current:
                # 숫자 5자리 + 소문자 M/T/R 패턴 확인
                match = re.match(r"^(\d{5})([mtr])$", current, re.IGNORECASE)
                if match:
                    number_part = match.group(1)
                    suffix = match.group(2).upper()
                    new_value = number_part + suffix
                    if new_value != current:
                        self.mk_entry.delete(0, tk.END)
                        self.mk_entry.insert(0, new_value)
        
        self.mk_entry.bind("<KeyRelease>", on_mk_entry_change_dialog)
        
        # M/T/R 버튼들
        btn_m = tk.Button(mk_frame, text="M", width=2, command=lambda: self.set_mk_suffix("M"))
        btn_m.pack(side=tk.LEFT, padx=1)
        
        btn_t = tk.Button(mk_frame, text="T", width=2, command=lambda: self.set_mk_suffix("T"))
        btn_t.pack(side=tk.LEFT, padx=1)
        
        btn_r = tk.Button(mk_frame, text="R", width=2, command=lambda: self.set_mk_suffix("R"))
        btn_r.pack(side=tk.LEFT, padx=1)
        
        # 공정명
        tk.Label(self.dialog, text="공정명:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.category_entry = Combobox(self.dialog, width=15, values=category_list, state="normal")
        self.category_entry.set(self.favorite_data["category"])
        self.category_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # 공정명 선택 시 작업코드 자동 변경
        def update_favorite_code_from_category(event=None):
            selected_category = self.category_entry.get().strip()
            if selected_category in category_code_mapping:
                self.code_entry.set(category_code_mapping[selected_category])
        
        self.category_entry.bind("<<ComboboxSelected>>", update_favorite_code_from_category)
        
        # 작업구분
        tk.Label(self.dialog, text="작업구분:", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        code_list = ["CAD", "KT", "KC", "TT", "ET"]
        self.code_entry = Combobox(self.dialog, width=15, values=code_list, state="normal")
        self.code_entry.set(self.favorite_data["code"])
        self.code_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
            # 업무내용
        tk.Label(self.dialog, text="업무내용:", font=("Arial", 12)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.task_text = tk.Text(self.dialog, width=30, height=8, wrap="word")
        self.task_text.insert("1.0", self.favorite_data["task"])
        self.task_text.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # 버튼
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="저장", command=self.save_favorite, width=10, bg="#4CAF50", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="초기화", command=self.reset_favorite, width=10, bg="#FF9800", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=self.cancel, width=10, bg="#f44336", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
    def set_mk_suffix(self, suffix):
        current = self.mk_entry.get().strip()
        # 숫자 5자리 + (영문자 1자리 있을 수도 있음)
        match = re.fullmatch(r"(\d{5})([mtrMTR]?)", current)
        if not match:
            messagebox.showwarning(
                "입력 오류",
                "MK번호는 숫자 5자리 또는 숫자 5자리+영문자(M/T/R) 형식이어야 합니다.\n예: 25001M"
            )
            return
        num_part = match.group(1)
        # 버튼의 suffix를 대문자로 붙임 (기존 영문자는 무시)
        self.mk_entry.delete(0, tk.END)
        self.mk_entry.insert(0, num_part + suffix.upper())
        
    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (350 // 2)
        self.dialog.geometry(f"350x350+{x}+{y}")
        
    def save_favorite(self):
        # 즐겨찾기명 검증 (15글자 미만 제한)
        favorite_name = self.name_entry.get().strip()
        if len(favorite_name) >= 15:
            return  # 메시지 박스 없이 그냥 저장하지 않음
        
        # MK번호 검증 (KC/TT의 경우 필수가 아님)
        mk_number = self.mk_entry.get().strip()
        code = self.code_entry.get().strip()
        
        if mk_number:  # MK번호가 입력된 경우에만 검증
            is_valid, error_msg = validate_mk_number(mk_number)
            if not is_valid:
                messagebox.showwarning("MK번호 오류", error_msg)
                return
        
        # KC/TT의 경우 MK번호가 없어도 허용
        if code in ["KC", "TT"] and not mk_number:
            pass  # MK번호 없이도 저장 가능
        elif code in ["CAD", "ET", "KT"] and not mk_number:
            messagebox.showwarning("MK번호 오류", "CAD/ET/KT 코드는 MK번호가 필요합니다.")
            return
        
        # 즐겨찾기 데이터 저장
        favorites[str(self.favorite_num)] = {
            "name": favorite_name,
            "mk_number": mk_number,
            "category": self.category_entry.get().strip(),
            "code": code,
            "task": self.task_text.get("1.0", tk.END).strip()
        }
        
        # 즐겨찾기 버튼 텍스트 업데이트
        self.update_favorite_button()
        
        # 설정 파일에 저장
        save_settings()
        
        self.dialog.destroy()
        
    def update_favorite_button(self):
        # 즐겨찾기 버튼 텍스트 업데이트
        if hasattr(self, 'favorite_button'):
            favorite_name = self.name_entry.get().strip()
            if favorite_name:
                # '_' 뒤 글자를 줄바꿈으로 표시 (간격 조정)
                if '_' in favorite_name:
                    parts = favorite_name.split('_', 1)
                    if len(parts) == 2:
                        display_text = f"{parts[0]}\n{parts[1]}"  # 간격을 절반으로 줄임
                        self.favorite_button.config(text=display_text)
                    else:
                        self.favorite_button.config(text=favorite_name)
                else:
                    self.favorite_button.config(text=favorite_name)
            else:
                self.favorite_button.config(text=f"즐겨찾기{self.favorite_num}")
                
    def reset_favorite(self):
        """즐겨찾기 설정을 초기화하는 함수"""
        # 모든 입력 필드를 빈칸으로 초기화
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, f"즐겨찾기{self.favorite_num}")
        
        self.mk_entry.delete(0, tk.END)
        
        self.category_entry.set("")
        
        self.code_entry.set("")
        
        self.task_text.delete("1.0", tk.END)
        
        # 즐겨찾기 데이터에서 해당 항목 제거
        favorite_key = str(self.favorite_num)
        if favorite_key in favorites:
            del favorites[favorite_key]
        
        # 설정 파일에 저장
        save_settings()
        
        # 즐겨찾기 버튼 텍스트 업데이트
        if hasattr(self, 'favorite_button'):
            self.favorite_button.config(text=f"즐겨찾기{self.favorite_num}")
    
    def cancel(self):
        self.dialog.destroy()

# 해야할 업무 설정 창
class TodoSettingDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("해야할 업무 등록")
        self.dialog.geometry("350x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.result = None
        
        # 해야할 업무 데이터
        self.todo_data = {
            "mk_number": "",
            "category": "",
            "code": "",
            "task": "",
            "deadline": ""
        }
        
        self.create_widgets()
        self.center_window()
        
    def create_widgets(self):
        # ESC 키로 창 닫기 바인딩
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
        
        # 창에 포커스 설정
        self.dialog.focus_set()
        
        # MK번호
        tk.Label(self.dialog, text="MK번호:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # MK번호 입력 프레임
        mk_frame = tk.Frame(self.dialog)
        mk_frame.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        self.mk_entry = tk.Entry(mk_frame, width=15, font=("Arial", 12))
        self.mk_entry.insert(0, self.todo_data["mk_number"])
        self.mk_entry.pack(side=tk.LEFT)
        
        # MK번호 입력 시 대문자 변환
        def on_mk_entry_change_dialog(*args):
            current = self.mk_entry.get()
            if current:
                # 숫자 5자리 + 소문자 M/T/R 패턴 확인
                match = re.match(r"^(\d{5})([mtr])$", current, re.IGNORECASE)
                if match:
                    number_part = match.group(1)
                    suffix = match.group(2).upper()
                    new_value = number_part + suffix
                    if new_value != current:
                        self.mk_entry.delete(0, tk.END)
                        self.mk_entry.insert(0, new_value)
        
        self.mk_entry.bind("<KeyRelease>", on_mk_entry_change_dialog)
        
        # M/T/R 버튼들
        btn_m = tk.Button(mk_frame, text="M", width=2, command=lambda: self.set_mk_suffix("M"))
        btn_m.pack(side=tk.LEFT, padx=1)
        
        btn_t = tk.Button(mk_frame, text="T", width=2, command=lambda: self.set_mk_suffix("T"))
        btn_t.pack(side=tk.LEFT, padx=1)
        
        btn_r = tk.Button(mk_frame, text="R", width=2, command=lambda: self.set_mk_suffix("R"))
        btn_r.pack(side=tk.LEFT, padx=1)
        
        # 공정명
        tk.Label(self.dialog, text="공정명:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.category_entry = Combobox(self.dialog, width=15, values=category_list, state="normal")
        self.category_entry.set(self.todo_data["category"])
        self.category_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # 공정명 선택 시 작업코드 자동 변경
        def update_todo_code_from_category(event=None):
            selected_category = self.category_entry.get().strip()
            if selected_category in category_code_mapping:
                self.code_entry.set(category_code_mapping[selected_category])
        
        self.category_entry.bind("<<ComboboxSelected>>", update_todo_code_from_category)
        
        # 작업구분
        tk.Label(self.dialog, text="작업구분:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        code_list = ["CAD", "KT", "KC", "TT", "ET"]
        self.code_entry = Combobox(self.dialog, width=15, values=code_list, state="normal")
        self.code_entry.set(self.todo_data["code"])
        self.code_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # 기한
        tk.Label(self.dialog, text="기한:", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        deadline_frame = tk.Frame(self.dialog)
        deadline_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        self.deadline_entry = tk.Entry(deadline_frame, width=15, font=("Arial", 12))
        self.deadline_entry.insert(0, self.todo_data["deadline"])
        self.deadline_entry.pack(side=tk.LEFT)
        
        self.deadline_button = tk.Button(deadline_frame, text="날짜 선택", command=self.select_date, 
                                       bg="#2196F3", fg="white", font=("Arial", 9))
        self.deadline_button.pack(side=tk.LEFT, padx=5)
        
        # 업무내용
        tk.Label(self.dialog, text="업무내용:", font=("Arial", 12)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.task_text = tk.Text(self.dialog, width=30, height=6, wrap="word")
        self.task_text.insert("1.0", self.todo_data["task"])
        self.task_text.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # 버튼
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="저장", command=self.save_todo, width=10, bg="#4CAF50", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="초기화", command=self.reset_form, width=10, bg="#FF9800", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=self.cancel, width=10, bg="#f44336", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
    def set_mk_suffix(self, suffix):
        current = self.mk_entry.get().strip()
        # 숫자 5자리 + (영문자 1자리 있을 수도 있음)
        match = re.fullmatch(r"(\d{5})([mtrMTR]?)", current)
        if not match:
            messagebox.showwarning(
                "입력 오류",
                "MK번호는 숫자 5자리 또는 숫자 5자리+영문자(M/T/R) 형식이어야 합니다.\n예: 25001M"
            )
            return
        num_part = match.group(1)
        # 버튼의 suffix를 대문자로 붙임 (기존 영문자는 무시)
        self.mk_entry.delete(0, tk.END)
        self.mk_entry.insert(0, num_part + suffix.upper())
        
    def select_date(self):
        """날짜 선택 (중복 방지)"""
        # 이미 캘린더 창이 열려있으면 포커스만 이동
        if hasattr(self, 'calendar_window') and self.calendar_window is not None:
            try:
                self.calendar_window.lift()
                self.calendar_window.focus_force()
                return
            except:
                pass
        
        if not CALENDAR_AVAILABLE or Calendar is None:
            messagebox.showerror("오류", "캘린더 라이브러리를 사용할 수 없습니다.")
            return
        
        try:
            self.calendar_window = tk.Toplevel(self.dialog)
            self.calendar_window.title("날짜 선택")
            self.calendar_window.geometry("300x250")
            self.calendar_window.resizable(False, False)
            self.calendar_window.transient(self.dialog)
            self.calendar_window.grab_set()
            self.calendar_window.focus_force()  # 창에 포커스 주기
            
            cal = Calendar(self.calendar_window, selectmode='day', date_pattern='yyyy-mm-dd')
            cal.pack(pady=20)
            
            def set_date():
                try:
                    selected_date = cal.get_date()
                    self.deadline_entry.delete(0, tk.END)
                    self.deadline_entry.insert(0, selected_date)
                    if self.calendar_window:
                        self.calendar_window.destroy()
                        self.calendar_window = None
                except Exception as e:
                    print(f"날짜 설정 오류: {e}")
                    if self.calendar_window:
                        self.calendar_window.destroy()
                        self.calendar_window = None
            
            # 즉시 날짜 선택
            def on_date_select(event):
                set_date()
            
            cal.bind("<<CalendarSelected>>", on_date_select)
            
            # 확인 버튼
            confirm_button = tk.Button(self.calendar_window, text="확인", command=set_date, 
                                     bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
            confirm_button.pack(pady=10)
            
            # 취소 버튼 추가
            cancel_button = tk.Button(self.calendar_window, text="취소", 
                                     command=lambda: self.calendar_window.destroy(), 
                                     bg="#f44336", fg="white", font=("Arial", 10, "bold"))
            cancel_button.pack(pady=5)
            
            # 창이 닫힐 때 변수 초기화
            def on_calendar_close():
                if self.calendar_window:
                    self.calendar_window.destroy()
                self.calendar_window = None
            
            # ESC 키로 창 닫기
            def on_escape(event):
                on_calendar_close()
            
            self.calendar_window.protocol("WM_DELETE_WINDOW", on_calendar_close)
            self.calendar_window.bind("<Escape>", on_escape)
            
        except Exception as e:
            print(f"날짜 선택 창 생성 실패: {e}")
            messagebox.showerror("오류", "날짜 선택 창을 생성할 수 없습니다.")
        
    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (350 // 2)
        self.dialog.geometry(f"350x350+{x}+{y}")
        
    def save_todo(self):
        # MK번호 검증 (KC/TT의 경우 필수가 아님)
        mk_number = self.mk_entry.get().strip()
        code = self.code_entry.get().strip()
        
        if mk_number:  # MK번호가 입력된 경우에만 검증
            is_valid, error_msg = validate_mk_number(mk_number)
            if not is_valid:
                messagebox.showwarning("MK번호 오류", error_msg)
                return
        
        # KC/TT의 경우 MK번호가 없어도 허용
        if code in ["KC", "TT"] and not mk_number:
            pass  # MK번호 없이도 저장 가능
        elif code in ["CAD", "ET", "KT"] and not mk_number:
            messagebox.showwarning("MK번호 오류", "CAD/ET/KT 코드는 MK번호가 필요합니다.")
            return
        
        # 해야할 업무 데이터 저장
        todo_id = str(len(todo_items) + 1)
        todo_items[todo_id] = {
            "mk_number": mk_number,
            "category": self.category_entry.get().strip(),
            "code": code,
            "task": self.task_text.get("1.0", tk.END).strip(),
            "deadline": self.deadline_entry.get().strip(),
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "important": False  # 중요 체크박스 기본값
        }
        
        # 설정 파일에 저장
        save_todo_settings()
        
        # 새 항목을 테이블에 직접 추가
        display_text = ""
        if mk_number:
            display_text += mk_number
        if self.category_entry.get().strip():
            if display_text:
                display_text += " - "
            display_text += self.category_entry.get().strip()
        if self.task_text.get("1.0", tk.END).strip():
            if display_text:
                display_text += " - "
            display_text += self.task_text.get("1.0", tk.END).strip()
        
        if not display_text:
            display_text = "내용 없음"
        
        # 기한 형식 변경 및 D-day 계산
        deadline = self.deadline_entry.get().strip()
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
                weekday_index = deadline_date.weekday()
                weekday_name = weekday_names[weekday_index]
                formatted_deadline = f"{deadline_date.strftime('%m-%d')} ({weekday_name})"
                
                today = datetime.now().date()
                d_day = (deadline_date.date() - today).days
                if d_day == 0:
                    d_day_text = "D-day"
                elif d_day > 0:
                    d_day_text = f"D-{d_day}"
                else:
                    d_day_text = f"D+{abs(d_day)}"
            except:
                formatted_deadline = deadline
                d_day_text = "날짜오류"
        else:
            formatted_deadline = "N"
            d_day_text = "N"
        

        
        # 새 항목을 테이블에 추가 (중요 기본값: 없음)
        todo_tree.insert("", "end", values=(
            "",  # 중요 표시 (기본값: 없음)
            display_text,
            datetime.now().strftime("%Y-%m-%d"),  # 등록일 (yyyy-mm-dd 형식)
            formatted_deadline,
            d_day_text
        ), tags=(todo_id,))
        

        
        self.dialog.destroy()
        
    def reset_form(self):
        """폼 초기화"""
        self.mk_entry.delete(0, tk.END)
        self.category_entry.set("")
        self.code_entry.set("")
        self.task_text.delete("1.0", tk.END)
        self.deadline_entry.delete(0, tk.END)
        
    def cancel(self):
        self.dialog.destroy()

# 해야할 일 등록 함수
def open_todo_setting():
    dialog = TodoSettingDialog(root)
    # 다이얼로그가 닫힌 후 테이블을 새로고침하지 않음

# 해야할 일 삭제 함수
def delete_todo_item(todo_id):
    if todo_id in todo_items:
        # 데이터에서 삭제
        del todo_items[todo_id]
        save_todo_settings()
        
        # 테이블에서 해당 항목만 찾아서 삭제
        for item in todo_tree.get_children():
            tags = todo_tree.item(item, 'tags')
            if tags and tags[0] == todo_id:
                todo_tree.delete(item)
                break

# 해야할 일 수정 함수 - TodoSettingDialog와 동일한 UI
def edit_todo_item(todo_id):
    if todo_id in todo_items:
        todo_data = todo_items[todo_id]
        
        # TodoSettingDialog와 동일한 창 생성
        edit_dialog = tk.Toplevel(root)
        edit_dialog.title("해야할 업무 수정")
        edit_dialog.geometry("350x350")
        edit_dialog.transient(root)
        edit_dialog.grab_set()
        
        # ESC 키로 창 닫기
        def on_escape(event):
            edit_dialog.destroy()
        
        edit_dialog.bind("<Escape>", on_escape)
        
        # 창에 포커스 설정
        edit_dialog.focus_set()
        
        # MK번호
        tk.Label(edit_dialog, text="MK번호:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # MK번호 입력 프레임
        mk_frame = tk.Frame(edit_dialog)
        mk_frame.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        mk_entry = tk.Entry(mk_frame, width=15, font=("Arial", 12))
        mk_entry.insert(0, todo_data.get("mk_number", ""))
        mk_entry.pack(side=tk.LEFT)
        
        # MK번호 입력 시 대문자 변환
        def on_mk_entry_change_dialog(*args):
            current = mk_entry.get()
            if current:
                # 숫자 5자리 + 소문자 M/T/R 패턴 확인
                match = re.match(r"^(\d{5})([mtr])$", current, re.IGNORECASE)
                if match:
                    number_part = match.group(1)
                    suffix = match.group(2).upper()
                    new_value = number_part + suffix
                    if new_value != current:
                        mk_entry.delete(0, tk.END)
                        mk_entry.insert(0, new_value)
        
        mk_entry.bind("<KeyRelease>", on_mk_entry_change_dialog)
        
        # M/T/R 버튼들
        btn_m = tk.Button(mk_frame, text="M", width=2, command=lambda: set_mk_suffix_edit("M"))
        btn_m.pack(side=tk.LEFT, padx=1)
        
        btn_t = tk.Button(mk_frame, text="T", width=2, command=lambda: set_mk_suffix_edit("T"))
        btn_t.pack(side=tk.LEFT, padx=1)
        
        btn_r = tk.Button(mk_frame, text="R", width=2, command=lambda: set_mk_suffix_edit("R"))
        btn_r.pack(side=tk.LEFT, padx=1)
        
        def set_mk_suffix_edit(suffix):
            current = mk_entry.get().strip()
            # 숫자 5자리 + (영문자 1자리 있을 수도 있음)
            match = re.fullmatch(r"(\d{5})([mtrMTR]?)", current)
            if not match:
                messagebox.showwarning(
                    "입력 오류",
                    "MK번호는 숫자 5자리 또는 숫자 5자리+영문자(M/T/R) 형식이어야 합니다.\n예: 25001M"
                )
                return
            num_part = match.group(1)
            # 버튼의 suffix를 대문자로 붙임 (기존 영문자는 무시)
            mk_entry.delete(0, tk.END)
            mk_entry.insert(0, num_part + suffix.upper())
        
        # 공정명
        tk.Label(edit_dialog, text="공정명:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        category_entry = Combobox(edit_dialog, width=15, values=category_list, state="normal")
        category_entry.set(todo_data.get("category", ""))
        category_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # 공정명 선택 시 작업코드 자동 변경
        def update_edit_code_from_category(event=None):
            selected_category = category_entry.get().strip()
            if selected_category in category_code_mapping:
                code_entry.set(category_code_mapping[selected_category])
        
        category_entry.bind("<<ComboboxSelected>>", update_edit_code_from_category)
        
        # 작업구분
        tk.Label(edit_dialog, text="작업구분:", font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        code_list = ["CAD", "KT", "KC", "TT", "ET"]
        code_entry = Combobox(edit_dialog, width=15, values=code_list, state="normal")
        code_entry.set(todo_data.get("code", ""))
        code_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # 기한
        tk.Label(edit_dialog, text="기한:", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        deadline_frame = tk.Frame(edit_dialog)
        deadline_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        deadline_entry = tk.Entry(deadline_frame, width=15, font=("Arial", 12))
        deadline_entry.insert(0, todo_data.get("deadline", ""))
        deadline_entry.pack(side=tk.LEFT)
        
        # 날짜선택 버튼 (중복 방지)
        calendar_window = [None]  # 리스트로 감싸서 참조 가능하게 함
        
        def select_date_edit():
            if calendar_window[0] is not None:
                try:
                    calendar_window[0].lift()
                    calendar_window[0].focus_force()
                    return
                except:
                    pass
            
            if not CALENDAR_AVAILABLE or Calendar is None:
                messagebox.showerror("오류", "캘린더 라이브러리를 사용할 수 없습니다.")
                return
            
            try:
                calendar_window[0] = tk.Toplevel(edit_dialog)
                calendar_window[0].title("날짜 선택")
                calendar_window[0].geometry("300x250")
                calendar_window[0].resizable(False, False)
                calendar_window[0].transient(edit_dialog)
                calendar_window[0].grab_set()
                calendar_window[0].focus_force()  # 창에 포커스 주기
                
                cal = Calendar(calendar_window[0], selectmode='day', date_pattern='yyyy-mm-dd')
                cal.pack(pady=20)
                
                def set_date():
                    try:
                        selected_date = cal.get_date()
                        deadline_entry.delete(0, tk.END)
                        deadline_entry.insert(0, selected_date)
                        if calendar_window[0]:
                            calendar_window[0].destroy()
                            calendar_window[0] = None
                    except Exception as e:
                        print(f"날짜 설정 오류: {e}")
                        if calendar_window[0]:
                            calendar_window[0].destroy()
                            calendar_window[0] = None
                
                def on_date_select(event):
                    set_date()
                
                cal.bind("<<CalendarSelected>>", on_date_select)
                
                confirm_button = tk.Button(calendar_window[0], text="확인", command=set_date, 
                                         bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
                confirm_button.pack(pady=10)
                
                # 취소 버튼 추가
                cancel_button = tk.Button(calendar_window[0], text="취소", 
                                         command=lambda: calendar_window[0].destroy(), 
                                         bg="#f44336", fg="white", font=("Arial", 10, "bold"))
                cancel_button.pack(pady=5)
                
                # 창이 닫힐 때 변수 초기화
                def on_calendar_close():
                    if calendar_window[0]:
                        calendar_window[0].destroy()
                    calendar_window[0] = None
                
                # ESC 키로 창 닫기
                def on_escape(event):
                    on_calendar_close()
                
                calendar_window[0].protocol("WM_DELETE_WINDOW", on_calendar_close)
                calendar_window[0].bind("<Escape>", on_escape)
                
            except Exception as e:
                print(f"날짜 선택 창 생성 실패: {e}")
                messagebox.showerror("오류", "날짜 선택 창을 생성할 수 없습니다.")
        
        deadline_button = tk.Button(deadline_frame, text="날짜 선택", command=select_date_edit, 
                                   bg="#2196F3", fg="white", font=("Arial", 9))
        deadline_button.pack(side=tk.LEFT, padx=5)
        
        # 업무내용
        tk.Label(edit_dialog, text="업무내용:", font=("Arial", 12)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        task_text = tk.Text(edit_dialog, width=30, height=6, wrap="word")
        task_text.insert("1.0", todo_data.get("task", ""))
        task_text.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # 버튼
        button_frame = tk.Frame(edit_dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def save_edit_todo():
            # MK번호 검증 (KC/TT의 경우 필수가 아님)
            mk_number = mk_entry.get().strip()
            code = code_entry.get().strip()
            
            if mk_number:  # MK번호가 입력된 경우에만 검증
                is_valid, error_msg = validate_mk_number(mk_number)
                if not is_valid:
                    messagebox.showwarning("MK번호 오류", error_msg)
                    return
            
            # KC/TT의 경우 MK번호가 없어도 허용
            if code in ["KC", "TT"] and not mk_number:
                pass  # MK번호 없이도 저장 가능
            elif code in ["CAD", "ET", "KT"] and not mk_number:
                messagebox.showwarning("MK번호 오류", "CAD/ET/KT 코드는 MK번호가 필요합니다.")
                return
            
            # 해야할 업무 데이터 업데이트 (덮어쓰기)
            todo_items[todo_id] = {
                "mk_number": mk_number,
                "category": category_entry.get().strip(),
                "code": code,
                "task": task_text.get("1.0", tk.END).strip(),
                "deadline": deadline_entry.get().strip(),
                "created_date": todo_data.get("created_date", datetime.now().strftime("%Y-%m-%d")),
                "important": todo_data.get("important", False)  # 기존 중요 상태 유지
            }
            
            # 설정 파일에 저장
            save_todo_settings()
            
            # 테이블 업데이트 (중요 표시 정렬 포함)
            update_todo_table()
            
            # 창 닫기
            edit_dialog.destroy()
        
        def reset_edit_form():
            """폼 초기화"""
            mk_entry.delete(0, tk.END)
            category_entry.set("")
            code_entry.set("")
            task_text.delete("1.0", tk.END)
            deadline_entry.delete(0, tk.END)
        
        tk.Button(button_frame, text="수정", command=save_edit_todo, width=10, bg="#4CAF50", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="초기화", command=reset_edit_form, width=10, bg="#FF9800", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=edit_dialog.destroy, width=10, bg="#f44336", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # 창 중앙 배치
        edit_dialog.update_idletasks()
        x = (edit_dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (edit_dialog.winfo_screenheight() // 2) - (350 // 2)
        edit_dialog.geometry(f"350x350+{x}+{y}")

# 해야할 일을 UI에 적용하는 함수
def apply_todo_to_ui(todo_id):
    if todo_id in todo_items:
        todo_data = todo_items[todo_id]
        
        # MK번호 입력
        mk_entry.delete(0, tk.END)
        mk_entry.insert(0, todo_data.get("mk_number", ""))
        
        # 공정명 입력
        category_entry.set(todo_data.get("category", ""))
        
        # 작업구분 입력
        code_entry.set(todo_data.get("code", ""))
        
        # 업무내용 입력
        task_entry.delete("1.0", tk.END)
        task_entry.insert("1.0", todo_data.get("task", ""))
        
        # 코드 업데이트 트리거
        update_code(None)

# 해야할 업무 테이블 업데이트 함수
def update_todo_table():
    """해야할 업무 테이블을 안전하게 업데이트 (중요 표시 정렬 포함)"""
    try:
        # 기존 항목 모두 삭제
        existing_items = list(todo_tree.get_children())
        for item in existing_items:
            todo_tree.delete(item)
        
        # 중요 항목과 일반 항목을 분리
        important_items = []
        normal_items = []
        
        for todo_id, todo_data in todo_items.items():
            # 표시할 텍스트 생성
            display_text = ""
            if todo_data["mk_number"]:
                display_text += todo_data["mk_number"]
            if todo_data["category"]:
                if display_text:
                    display_text += " - "
                display_text += todo_data["category"]
            if todo_data["task"]:
                if display_text:
                    display_text += " - "
                display_text += todo_data["task"]
            
            if not display_text:
                display_text = "내용 없음"
            
            # 등록일 형식 변경 (yyyy-mm-dd)
            created_date = todo_data.get("created_date", "")
            if created_date:
                try:
                    date_obj = datetime.strptime(created_date, "%Y-%m-%d")
                    formatted_created_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_created_date = created_date
            else:
                formatted_created_date = "N"
            
            # 기한 형식 변경 및 D-day 계산
            deadline = todo_data.get("deadline", "")
            if deadline:
                try:
                    # 기한 형식을 mm-dd (요일) 형식으로 변경
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
                    weekday_index = deadline_date.weekday()  # 0=월요일, 6=일요일
                    weekday_name = weekday_names[weekday_index]
                    formatted_deadline = f"{deadline_date.strftime('%m-%d')} ({weekday_name})"
                    
                    # D-day 계산
                    today = datetime.now().date()
                    d_day = (deadline_date.date() - today).days
                    if d_day == 0:
                        d_day_text = "D-day"
                    elif d_day > 0:
                        d_day_text = f"D-{d_day}"
                    else:
                        d_day_text = f"D+{abs(d_day)}"
                except:
                    formatted_deadline = deadline
                    d_day_text = "날짜오류"
            else:
                # 기한이 없으면 'N'으로 표시
                formatted_deadline = "N"
                d_day_text = "N"
            
            # 중요 표시 - ✅ 아이콘 사용
            important_status = "✅" if todo_data.get("important", False) else ""
            
            # 항목 데이터 준비
            item_data = {
                'todo_id': todo_id,
                'values': (
                    important_status,  # 중요 체크박스
                    display_text,
                    formatted_created_date,
                    formatted_deadline,
                    d_day_text
                ),
                'tags': (todo_id,),
                'important': todo_data.get("important", False)
            }
            
            # 중요 항목과 일반 항목 분리
            if todo_data.get("important", False):
                important_items.append(item_data)
            else:
                normal_items.append(item_data)
        
        # 중요 항목을 최상단에 추가 (인덱스 0부터 시작)
        for i, item_data in enumerate(important_items):
            todo_tree.insert("", i, values=item_data['values'], tags=item_data['tags'])
        
        # 일반 항목을 중요 항목 다음에 추가
        for item_data in normal_items:
            todo_tree.insert("", "end", values=item_data['values'], tags=item_data['tags'])
        
        # 설정 저장 (업데이트 후에만)
        save_todo_settings()
        
    except Exception as e:
        print(f"해야할 업무 테이블 업데이트 중 오류: {e}")

def refresh_todo_table():
    """해야할 업무 테이블을 새로고침 (선택 상태 유지)"""
    update_todo_table()

# 즐겨찾기 설정 함수
def open_favorite_setting(favorite_num, button):
    dialog = FavoriteSettingDialog(root, favorite_num)
    dialog.favorite_button = button  # 버튼 참조 전달

# 즐겨찾기 적용 함수
def apply_favorite(favorite_num):
    favorite_key = str(favorite_num)
    if favorite_key in favorites:
        data = favorites[favorite_key]
        
        # MK번호 설정
        mk_entry.delete(0, tk.END)
        mk_entry.insert(0, data["mk_number"])
        
        # 공정명 설정
        category_entry.set(data["category"])
        
        # 코드 설정
        code_entry.set(data["code"])
        
        # 업무내용 설정
        task_entry.delete("1.0", tk.END)
        task_entry.insert("1.0", data["task"])

# MK번호 검증 함수
def validate_mk_number(mk_number):
    """MK번호 검증 함수 (5글자 숫자 + 알파벳 M/T/R)"""
    if not mk_number:
        return True, ""  # 빈 값은 허용
    
    # 정규식 패턴: 5자리 숫자 + 필수 알파벳(M/T/R)
    pattern = re.compile(r"^\d{5}[MTRmtr]$")
    
    if not pattern.match(mk_number):
        return False, "MK번호는 5자리 숫자 + 알파벳(M/T/R)이어야 합니다.\n예: 25001M, 25002T, 25003R"
    
    return True, ""

# MK번호 버튼 기능
def set_mk_suffix(suffix):
    current = mk_entry.get().strip()
    # 숫자 5자리만 있는지 확인 (M/T/R 문자가 있어도 허용)
    if re.match(r"^\d{5}[MTRmtr]?$", current):
        # 숫자 5자리 부분만 추출하고 새로운 suffix 추가
        number_part = current[:5]
        mk_entry.delete(0, tk.END)
        mk_entry.insert(0, number_part + suffix.upper())
        update_code(None)
    else:
        messagebox.showwarning(
            "입력 오류",
            "MK번호는 숫자 5자리만 입력한 후 M/T/R 버튼을 클릭해주세요.\n예: 25001 입력 후 M 버튼 클릭"
        )

def convert_mk_to_uppercase(mk_number):
    """MK번호의 M/T/R 부분을 대문자로 변환"""
    if not mk_number:
        return mk_number
    
    # 숫자 5자리 + 소문자 M/T/R 패턴 확인
    match = re.match(r"^(\d{5})([mtr])$", mk_number, re.IGNORECASE)
    if match:
        number_part = match.group(1)
        suffix = match.group(2).upper()
        return number_part + suffix
    
    return mk_number




# 오른쪽 테이블 더블 클릭 이벤트
def on_double_click(event):
    # 더블클릭 시 로그 편집 창 열기
    if tree.selection():
        edit_log_entry()

# UI 구성

# 로그 추가 함수
def add_log_entry():
    dialog = tk.Toplevel(root)
    dialog.title("로그 추가")
    dialog.geometry("600x700")
    dialog.resizable(True, True)
    dialog.transient(root)
    dialog.grab_set()
    
    # ESC 키로 창 닫기
    def on_escape(event):
        dialog.destroy()
    
    dialog.bind("<Escape>", on_escape)
    
    # 창에 포커스 설정
    dialog.focus_set()
    
    # 메인 프레임
    main_frame = tk.Frame(dialog, bg="#f5f5f5")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # 제목
    title_label = tk.Label(main_frame, text="새 로그 추가", font=("Arial", 16, "bold"), bg="#f5f5f5", fg="#333333")
    title_label.pack(pady=(0, 20))
    
    # 입력 프레임
    input_frame = tk.Frame(main_frame, bg="#f5f5f5")
    input_frame.pack(fill="both", expand=True)
    
    # 날짜 섹션
    date_frame = tk.LabelFrame(input_frame, text="날짜", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    date_frame.pack(fill="x", pady=(0, 15))
    
    date_inner_frame = tk.Frame(date_frame, bg="#f5f5f5")
    date_inner_frame.pack()
    
    year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
    month_var = tk.StringVar(value=datetime.now().strftime("%m"))
    day_var = tk.StringVar(value=datetime.now().strftime("%d"))
    
    year_entry = tk.Entry(date_inner_frame, width=6, textvariable=year_var, font=("Arial", 11), relief="solid", bd=1)
    year_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="년", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    month_entry = tk.Entry(date_inner_frame, width=4, textvariable=month_var, font=("Arial", 11), relief="solid", bd=1)
    month_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="월", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    day_entry = tk.Entry(date_inner_frame, width=4, textvariable=day_var, font=("Arial", 11), relief="solid", bd=1)
    day_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="일", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 시간 섹션
    time_frame = tk.LabelFrame(input_frame, text="시간", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    time_frame.pack(fill="x", pady=(0, 15))
    
    # 시작시간
    start_time_frame = tk.Frame(time_frame, bg="#f5f5f5")
    start_time_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(start_time_frame, text="시작시간", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    sh_var = tk.StringVar(value=datetime.now().strftime("%H"))
    sm_var = tk.StringVar(value=datetime.now().strftime("%M"))
    
    sh_entry = tk.Entry(start_time_frame, width=4, textvariable=sh_var, font=("Arial", 11), relief="solid", bd=1)
    sh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(start_time_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    sm_entry = tk.Entry(start_time_frame, width=4, textvariable=sm_var, font=("Arial", 11), relief="solid", bd=1)
    sm_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(start_time_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 완료시간
    end_time_frame = tk.Frame(time_frame, bg="#f5f5f5")
    end_time_frame.pack(fill="x")
    
    tk.Label(end_time_frame, text="완료시간", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    eh_var = tk.StringVar(value=datetime.now().strftime("%H"))
    em_var = tk.StringVar(value=datetime.now().strftime("%M"))
    
    eh_entry = tk.Entry(end_time_frame, width=4, textvariable=eh_var, font=("Arial", 11), relief="solid", bd=1)
    eh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(end_time_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    em_entry = tk.Entry(end_time_frame, width=4, textvariable=em_var, font=("Arial", 11), relief="solid", bd=1)
    em_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(end_time_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 소요시간 (자동 계산)
    duration_frame = tk.LabelFrame(input_frame, text="소요시간 (자동 계산)", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    duration_frame.pack(fill="x", pady=(0, 15))
    
    duration_inner_frame = tk.Frame(duration_frame, bg="#f5f5f5")
    duration_inner_frame.pack()
    
    dh_var = tk.StringVar(value="0")
    dm_var = tk.StringVar(value="0")
    ds_var = tk.StringVar(value="0")
    
    dh_entry = tk.Entry(duration_inner_frame, width=4, textvariable=dh_var, font=("Arial", 11), relief="solid", bd=1, state="readonly")
    dh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    dm_entry = tk.Entry(duration_inner_frame, width=4, textvariable=dm_var, font=("Arial", 11), relief="solid", bd=1, state="readonly")
    dm_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    ds_entry = tk.Entry(duration_inner_frame, width=4, textvariable=ds_var, font=("Arial", 11), relief="solid", bd=1, state="readonly")
    ds_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="초", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # ESC 키로 창 닫기
    def on_escape(event):
        dialog.destroy()
    
    dialog.bind("<Escape>", on_escape)
    
    # 작업 정보 섹션
    work_frame = tk.LabelFrame(input_frame, text="작업 정보", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    work_frame.pack(fill="x", pady=(0, 15))
    
    # 작업코드
    code_frame = tk.Frame(work_frame, bg="#f5f5f5")
    code_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(code_frame, text="작업코드", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    code_var = tk.StringVar()
    code_combo = ttk.Combobox(code_frame, textvariable=code_var, values=["CAD", "KT", "ET", "KC", "TT"], width=15, state="readonly", font=("Arial", 11))
    code_combo.pack(side=tk.LEFT)
    
    # MK번호
    mk_frame = tk.Frame(work_frame, bg="#f5f5f5")
    mk_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(mk_frame, text="MK번호", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    mknum_var = tk.StringVar()
    mk_entry_dialog = tk.Entry(mk_frame, width=12, textvariable=mknum_var, font=("Arial", 11), relief="solid", bd=1)
    mk_entry_dialog.pack(side=tk.LEFT, padx=(0, 5))
    
    def set_mk_suffix_dialog(suffix):
        val = mk_entry_dialog.get().strip()
        # 숫자 5자리만 있는지 확인 (M/T/R 문자가 있어도 허용)
        if re.match(r"^\d{5}[MTRmtr]?$", val):
            # 숫자 5자리 부분만 추출하고 새로운 suffix 추가
            number_part = val[:5]
            mk_entry_dialog.delete(0, tk.END)
            mk_entry_dialog.insert(0, number_part + suffix)
        elif val.isdigit() and len(val) == 5:
            # 숫자 5자리만 있는 경우
            mk_entry_dialog.delete(0, tk.END)
            mk_entry_dialog.insert(0, val + suffix)
    
    for suffix, btn_text in [("M", "M"), ("T", "T"), ("R", "R")]:
        btn = tk.Button(mk_frame, text=btn_text, width=2, command=lambda s=suffix: set_mk_suffix_dialog(s), 
                       font=("Arial", 10), relief="solid", bd=1, bg="#e0e0e0")
        btn.pack(side=tk.LEFT, padx=2)
    
    # 공정명
    category_frame = tk.Frame(work_frame, bg="#f5f5f5")
    category_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(category_frame, text="공정명", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    category_var = tk.StringVar()
    category_combo = ttk.Combobox(category_frame, textvariable=category_var, values=category_list, width=25, font=("Arial", 11))
    category_combo.pack(side=tk.LEFT)
    
    # 공정명 선택 시 작업코드 자동 연동
    def update_code_from_category_dialog(event=None):
        selected_category = category_var.get()
        print(f"공정명 선택됨: {selected_category}")  # 디버깅용
        if selected_category:
            # 기존 category_code_mapping 사용
            if selected_category in category_code_mapping:
                code_var.set(category_code_mapping[selected_category])
                print(f"작업코드 설정됨: {category_code_mapping[selected_category]}")  # 디버깅용
            else:
                print(f"매핑되지 않은 공정명: {selected_category}")  # 디버깅용
    
    # 공정명 콤보박스에 이벤트 바인딩
    category_combo.bind("<<ComboboxSelected>>", update_code_from_category_dialog)
    category_combo.bind("<KeyRelease>", update_code_from_category_dialog)
    category_combo.bind("<FocusOut>", update_code_from_category_dialog)
    
    # 업무내용
    task_frame = tk.Frame(work_frame, bg="#f5f5f5")
    task_frame.pack(fill="x")
    
    tk.Label(task_frame, text="업무내용", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    task_text = tk.Text(task_frame, width=40, height=4, font=("Arial", 11), relief="solid", bd=1)
    task_text.pack(side=tk.LEFT, fill="x", expand=True)
    
    def update_duration(*args):
        try:
            start_h = int(sh_var.get() or 0)
            start_m = int(sm_var.get() or 0)
            end_h = int(eh_var.get() or 0)
            end_m = int(em_var.get() or 0)
            
            start_total = start_h * 60 + start_m
            end_total = end_h * 60 + end_m
            
            if end_total >= start_total:
                diff_minutes = end_total - start_total
                hours = diff_minutes // 60
                minutes = diff_minutes % 60
                seconds = 0
            else:
                hours = minutes = seconds = 0
            
            dh_var.set(str(hours))
            dm_var.set(str(minutes))
            ds_var.set(str(seconds))
        except ValueError:
            pass
    
    # 시간 변수들에 트레이스 추가
    sh_var.trace_add("write", update_duration)
    sm_var.trace_add("write", update_duration)
    eh_var.trace_add("write", update_duration)
    em_var.trace_add("write", update_duration)
    
    def save_log():
        try:
            # MK번호 검증
            mk_number = mknum_var.get().strip()
            code = code_var.get().strip()
            
            if mk_number:  # MK번호가 입력된 경우에만 검증
                is_valid, error_msg = validate_mk_number(mk_number)
                if not is_valid:
                    messagebox.showwarning("MK번호 오류", error_msg)
                    return
            
            date_str = f"{year_var.get()}-{month_var.get().zfill(2)}-{day_var.get().zfill(2)}"
            start_time_str = f"{sh_var.get().zfill(2)}시 {sm_var.get().zfill(2)}분"
            end_time_str = f"{eh_var.get().zfill(2)}시 {em_var.get().zfill(2)}분"
            duration_str = f"{dh_var.get().zfill(2)}시 {dm_var.get().zfill(2)}분 {ds_var.get().zfill(2)}초"
            
            new_values = (
                date_str,
                start_time_str,
                end_time_str,
                code_var.get(),
                mknum_var.get(),
                category_var.get(),
                task_text.get("1.0", tk.END).strip(),
                duration_str
            )
            tree.insert("", "end", values=new_values)
            
            # 실제 로그 파일에도 추가 (오늘기록 보기에서도 원본 파일에 반영)
            start_datetime = f"{date_str} {sh_var.get().zfill(2)}:{sm_var.get().zfill(2)}:00"
            end_datetime = f"{date_str} {eh_var.get().zfill(2)}:{em_var.get().zfill(2)}:00"
            
            # 로그 파일에 업무 시작/종료 기록 추가
            log_entry_start = f"[{start_datetime}] 업무 시작\n"
            log_entry_end = f"[{end_datetime}] 업무 종료 - 코드: {code_var.get()}"
            
            if mknum_var.get():
                log_entry_end += f", MK번호: {mknum_var.get()}"
            if category_var.get():
                log_entry_end += f", 작업분류: {category_var.get()}"
            if task_text.get("1.0", tk.END).strip():
                log_entry_end += f", 작업: {task_text.get('1.0', tk.END).strip()}"
            
            log_entry_end += f" (소요 시간: {dh_var.get()}시간 {dm_var.get()}분 {ds_var.get()}초)\n"
            
            with open(LOG_FILE, "a", encoding="utf-8") as file:
                file.write(log_entry_start)
                file.write(log_entry_end)
            
            # 시작시간 기준 자동 정렬
            all_items = [(tree.set(iid, '시작시간'), iid) for iid in tree.get_children()]
            all_items.sort(key=lambda x: x[0])
            for idx, (_, iid) in enumerate(all_items):
                tree.move(iid, '', idx)
            dialog.destroy()
            
            # 현재 정렬 상태 유지 (UI 새로고침 제거)
            if sort_column in column_sort_states:
                sort_treeview(sort_column)
        except Exception as e:
            messagebox.showerror("오류", f"로그 추가 실패: {e}")
    
    # 버튼 프레임
    button_frame = tk.Frame(main_frame, bg="#f5f5f5")
    button_frame.pack(pady=20)
    
    save_button = tk.Button(button_frame, text="저장", command=save_log, 
                           bg="#4caf50", fg="white", font=("Arial", 12, "bold"), 
                           width=10, height=2, relief="flat")
    save_button.pack(side=tk.LEFT, padx=5)
    
    cancel_button = tk.Button(button_frame, text="취소", command=dialog.destroy,
                             bg="#f44336", fg="white", font=("Arial", 12, "bold"),
                             width=10, height=2, relief="flat")
    cancel_button.pack(side=tk.LEFT, padx=5)

def set_button_hotkey(button, label):
    def on_key_press(event):
        key = event.keysym
        if key == "Escape":
            dialog.destroy()
            return
        
        # 기존 단축키 제거
        if button in button_hotkeys:
            old_key = button_hotkeys[button]
            root.unbind(f"<{old_key}>")
        
        # 새 단축키 설정
        button_hotkeys[button] = key
        root.bind(f"<{key}>", lambda e: button.invoke())
        
        # 버튼 텍스트 업데이트
        original_text = button.cget("text")
        if "(" in original_text:
            original_text = original_text.split("(")[0].strip()
        
        # 기존 버튼 폰트 설정 유지
        current_font = button.cget("font")
        if isinstance(current_font, str):
            font_parts = current_font.split()
            if len(font_parts) >= 2:
                font_family = font_parts[0]
                font_size = font_parts[1]
                font_weight = font_parts[2] if len(font_parts) > 2 else "normal"
                new_font = (font_family, font_size, font_weight)
            else:
                new_font = current_font
        else:
            new_font = current_font
        
        button.config(text=f"{original_text} ({key})", font=new_font)
        
        # 설정 파일에 저장
        save_settings()
        
        dialog.destroy()
    
    def reset_hotkey():
        # 기존 단축키 제거
        if button in button_hotkeys:
            old_key = button_hotkeys[button]
            root.unbind(f"<{old_key}>")
            del button_hotkeys[button]
        
        # 버튼 텍스트에서 단축키 제거
        original_text = button.cget("text")
        if "(" in original_text:
            original_text = original_text.split("(")[0].strip()
        
        # 기존 버튼 폰트 설정 유지
        current_font = button.cget("font")
        if isinstance(current_font, str):
            font_parts = current_font.split()
            if len(font_parts) >= 2:
                font_family = font_parts[0]
                font_size = font_parts[1]
                font_weight = font_parts[2] if len(font_parts) > 2 else "normal"
                new_font = (font_family, font_size, font_weight)
            else:
                new_font = current_font
        else:
            new_font = current_font
        
        button.config(text=original_text, font=new_font)
        
        # 설정 파일에 저장
        save_settings()
        
        dialog.destroy()
    
    dialog = tk.Toplevel(root)
    dialog.title(f"{label} 단축키 설정")
    dialog.geometry("300x150")
    dialog.resizable(False, False)
    
    # ESC 키로 창 닫기 바인딩
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    label_text = tk.Label(dialog, text=f"{label} 버튼의 단축키를 입력하세요:\n(ESC: 취소)", font=("Arial", 12))
    label_text.pack(pady=20)
    
    # 버튼 프레임
    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)
    
    # 초기화 버튼
    reset_button = tk.Button(button_frame, text="초기화", command=reset_hotkey, 
                            bg="#f44336", fg="white", width=8)
    reset_button.pack(side=tk.LEFT, padx=5)
    
    # 취소 버튼
    cancel_button = tk.Button(button_frame, text="취소", command=dialog.destroy,
                             bg="#9e9e9e", fg="white", width=8)
    cancel_button.pack(side=tk.LEFT, padx=5)
    
    dialog.focus_set()
    dialog.bind("<Key>", on_key_press)
    dialog.grab_set()

root = tk.Tk()
root.title("MK 업무기록 프로그램 v1.1")
root.geometry("1800x850") # 창 크기 조정 - 내용이 딱 보일 정도로
root.configure(bg="#f5f5f5") # 배경색 설정

# ESC 키로 메인 창 닫기
def on_main_escape(event):
    on_closing()

root.bind("<Escape>", on_main_escape)

# 스타일 설정
style = ttk.Style()
style.theme_use('clam')
style.configure('Treeview', rowheight=25, font=('Arial', 10))
style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))



# 프레임 구조
main_frame = tk.Frame(root, bg="#F5F5F5")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 왼쪽 프레임 (업무 입력)
left_frame = tk.Frame(main_frame, width=500, bg="#F8F9FA", relief="flat", bd=1)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

# 오른쪽 프레임 (로그)
right_frame = tk.Frame(main_frame, bg="#F8F9FA", relief="flat", bd=1)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# 현재 시간 표시
current_time_var = tk.StringVar()
def update_time():
    current_time_var.set("현재시간: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    root.after(1000, update_time)

time_label = tk.Label(left_frame, textvariable=current_time_var, font=("Arial", 12, "bold"), 
                     bg="#F8F9FA", fg="#333333")
time_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)
update_time()

# 공지사항 버튼들
notice_frame = tk.Frame(left_frame, bg="#F8F9FA")
notice_frame.grid(row=0, column=2, padx=5, pady=10, sticky="w")

usage_button = tk.Button(notice_frame, text="사용법", command=show_notice, 
                        bg="#E0E0E0", fg="black", width=8, height=1, font=("Arial", 9))
usage_button.pack(side=tk.LEFT, padx=2)

update_button = tk.Button(notice_frame, text="업데이트 v1.1", command=show_notice,
                         bg="#E0E0E0", fg="black", width=10, height=1, font=("Arial", 9))
update_button.pack(side=tk.LEFT, padx=2)

# 왼쪽 프레임 내용 ## ====== RESET ======
reset_button = tk.Button(left_frame, text="RESET", font=("Arial", 11, "bold"), width=12, height=2, 
                        command=reset_work, bg="#4CAF50", fg="white", relief="raised", bd=3)
reset_button.grid(row=1, column=0, padx=(10,5), pady=10, sticky="w")
reset_button.bind("<Button-3>", lambda e: set_button_hotkey(reset_button, "RESET"))

# 획기적인 방법: START와 END 버튼을 하나의 프레임에 넣어서 완전히 붙이기
button_frame = tk.Frame(left_frame, bg="#F8F9FA")
button_frame.grid(row=1, column=1, columnspan=2, pady=10, sticky="w")

## ====== 업무시작=========
start_button = tk.Button(button_frame, text="START", font=("Arial", 11, "bold"), width=12, height=2, 
                        command=start_work, bg="#2196F3", fg="white", relief="raised", bd=3)
start_button.grid(row=0, column=0, padx=(5,5), pady=0, sticky="w")
start_button.bind("<Button-3>", lambda e: set_button_hotkey(start_button, "START"))

## ====== 업무종료=====
end_button = tk.Button(button_frame, text="END", width=12, height=2, font=("Arial", 11, "bold"), 
                      command=end_work, bg="#f44336", fg="white", relief="raised", bd=3)
end_button.grid(row=0, column=1, padx=(5,10), pady=0, sticky="w")
end_button.bind("<Button-3>", lambda e: set_button_hotkey(end_button, "END"))

# 현재 업무 소요시간 표시 라벨 (한 줄로 통합)
work_duration_var = tk.StringVar(value="현재 업무 소요시간\n00 : 00")
work_duration_label = tk.Label(left_frame, textvariable=work_duration_var, font=("맑은 고딕", 13, "bold"), fg="#2E7D32", bg="#F8F9FA")
work_duration_label.grid(row=1, column=2, padx=(5,5), pady=6, sticky="w")

# 실시간 타이머 관련 변수
work_timer_thread = None
work_timer_running = False

def update_work_duration_thread():
    global work_timer_running
    while work_timer_running:
        if start_time is not None:
            elapsed = int((datetime.now() - start_time).total_seconds())
            minutes = elapsed // 60
            seconds = elapsed % 60
            # GUI 업데이트는 메인 스레드에서 실행
            root.after(0, lambda: work_duration_var.set(f"현재 업무 소요시간\n{minutes:02d} : {seconds:02d}"))
        time.sleep(1)

def start_work_timer():
    global work_timer_thread, work_timer_running
    if work_timer_thread is None or not work_timer_thread.is_alive():
        work_timer_running = True
        work_timer_thread = threading.Thread(target=update_work_duration_thread, daemon=True)
        work_timer_thread.start()

def stop_work_timer():
    global work_timer_running
    work_timer_running = False
    work_duration_var.set("현재 업무 소요시간\n00 : 00")

# MK번호 입력란 + 버튼
mk_label = tk.Label(left_frame, text="MK 번호:", font=("Arial", 12, "bold"), 
                    bg="#F8F9FA", fg="#333333")
mk_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")

mk_frame = tk.Frame(left_frame, bg="#F8F9FA")
mk_frame.grid(row=3, column=1, sticky="w", padx=10, pady=10)

mk_entry = tk.Entry(mk_frame, font=("Arial", 15), width=13)
mk_entry.pack(side=tk.LEFT)
mk_entry.bind("<FocusOut>", lambda event: update_code(None)) # 포커스 아웃 시 코드 업데이트

# MK번호 입력 시 대문자 변환
def on_mk_entry_change(*args):
    current = mk_entry.get()
    if current:
        # 숫자 5자리 + 소문자 M/T/R 패턴 확인
        match = re.match(r"^(\d{5})([mtr])$", current, re.IGNORECASE)
        if match:
            number_part = match.group(1)
            suffix = match.group(2).upper()
            new_value = number_part + suffix
            if new_value != current:
                mk_entry.delete(0, tk.END)
                mk_entry.insert(0, new_value)

mk_entry.bind("<KeyRelease>", on_mk_entry_change)

btn_m = tk.Button(mk_frame, text="M", width=2, command=lambda: set_mk_suffix("M"))
btn_m.pack(side=tk.LEFT, padx=1)

btn_t = tk.Button(mk_frame, text="T", width=2, command=lambda: set_mk_suffix("T"))
btn_t.pack(side=tk.LEFT, padx=1)

btn_r = tk.Button(mk_frame, text="R", width=2, command=lambda: set_mk_suffix("R"))
btn_r.pack(side=tk.LEFT, padx=1)

# 작업분류 콤보박스 + 코드 표시
code_label = tk.Label(left_frame, text="공정명:", font=("Arial", 12, "bold"), 
                     bg="#F8F9FA", fg="#333333")
code_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

category_entry = Combobox(left_frame, width=25, values=category_list, state="normal", font=("Arial", 12))
category_entry.grid(row=4, column=1, sticky="w", padx=10, pady=10)
category_entry.bind("<<ComboboxSelected>>", lambda event: [update_code(event), update_code_from_category(event)])

code_entry = ttk.Combobox(left_frame, font=("Arial", 12), width=5, values=["CAD", "KT", "ET", "KC", "TT"], state="readonly")
code_entry.grid(row=4, column=2, sticky="w", padx=10, pady=10)

# 즐겨찾기 버튼 프레임
favorite_frame_1 = tk.Frame(left_frame, bg="#F8F9FA")
favorite_frame_1.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

favorite_frame_2 = tk.Frame(left_frame, bg="#F8F9FA")
favorite_frame_2.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

button_width, button_height = 12, 3
button_bg = "#e3f2fd"

# 즐겨찾기 버튼 생성
global favorite_buttons
favorite_buttons = []
for i in range(8):
    favorite_num = i + 1
    if i < 4:
        button = tk.Button(favorite_frame_1, text=f"즐겨찾기{favorite_num}", 
                          command=lambda num=favorite_num: apply_favorite(num), 
                          width=button_width, bg=button_bg, height=button_height, font=("Arial", 11))
        button.grid(row=0, column=i, padx=3, pady=2)
    else:
        button = tk.Button(favorite_frame_2, text=f"즐겨찾기{favorite_num}", 
                          command=lambda num=favorite_num: apply_favorite(num), 
                          width=button_width, bg=button_bg, height=button_height, font=("Arial", 11))
        button.grid(row=0, column=i % 4, padx=3, pady=2)
    
    # 오른쪽 클릭으로 설정 창 열기
    button.bind("<Button-3>", lambda event, num=favorite_num, btn=button: open_favorite_setting(num, btn))
    favorite_buttons.append(button)

# 즐겨찾기 버튼 생성 완료 후 설정 적용 (UI 완전 생성 후)
print("즐겨찾기 버튼 생성 완료")

# UI 생성 완료 후 설정 적용
def apply_settings_after_ui():
    # 설정 로딩
    load_settings_later()
    
    # UI에 설정 적용
    apply_saved_settings()
    
    # 해야할 일 테이블 초기화
    init_todo_table()
    
    print("UI 생성 완료 - 설정 적용 시작")
    print("설정 적용 완료")

# 프로그램 시작 시 설정 적용
root.after(100, apply_settings_after_ui)

# 업무 내용
task_label = tk.Label(left_frame, text="업무 내용:", font=("Arial", 12, "bold"), 
                     bg="#F8F9FA", fg="#333333")
task_label.grid(row=7, column=0, padx=10, pady=10, sticky="ne")

task_frame = tk.Frame(left_frame, bg="#F8F9FA", relief="solid", bd=1)
task_frame.grid(row=7, column=1, columnspan=2, sticky="wens", padx=10, pady=10)

# 작업내용 텍스트 영역
task_text_frame = tk.Frame(task_frame)
task_text_frame.pack(side="left", fill="both", expand=True)

task_scroll = tk.Scrollbar(task_text_frame, orient="vertical")
task_entry = tk.Text(task_text_frame, wrap="word", yscrollcommand=task_scroll.set, height=12, width=15)
task_scroll.config(command=task_entry.yview)

task_entry.pack(side="left", fill="both", expand=True)
task_scroll.pack(side="right", fill="y")

status_label = tk.Label(left_frame, text="업무대기", fg="#2196F3", font=("맑은 고딕", 13, "bold"),
                       bg="#F8F9FA")
status_label.grid(row=3, column=2, padx=10, pady=10, sticky="w")

## ====== 업무종료=====
# END 버튼 제거 - START/END 버튼으로 대체

root.bind("<Control-v>", paste_from_clipboard)

# 해야할 업무 프레임
todo_frame = tk.Frame(left_frame, bg="#F8F9FA")
todo_frame.grid(row=9, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

# 해야할 업무 제목 프레임 (제목 + 버튼)
todo_title_frame = tk.Frame(todo_frame, bg="#F8F9FA")
todo_title_frame.pack(pady=(0, 5), fill=tk.X)

todo_title = tk.Label(todo_title_frame, text="해야할 업무", font=("Arial", 12, "bold"), 
                      bg="#F8F9FA", fg="#333333")
todo_title.pack(side=tk.LEFT)

# 등록/삭제 버튼 프레임
todo_button_frame = tk.Frame(todo_title_frame, bg="#F8F9FA")
todo_button_frame.pack(side=tk.RIGHT)

# 등록 버튼
todo_add_button = tk.Button(todo_button_frame, text="등록", 
                           command=open_todo_setting,
                           bg="#4CAF50", fg="white", font=("Arial", 9),
                           width=6, height=1)
todo_add_button.pack(side=tk.LEFT, padx=(0, 5))

# 삭제 버튼
def delete_selected_todos():
    """선택된 항목들을 삭제"""
    selected_items = todo_tree.selection()
    if selected_items:
        for item in selected_items:
            tags = todo_tree.item(item, 'tags')
            if tags:
                delete_todo_item(tags[0])

todo_delete_button = tk.Button(todo_button_frame, text="삭제", 
                              command=delete_selected_todos,
                              bg="#f44336", fg="white", font=("Arial", 9),
                              width=6, height=1)
todo_delete_button.pack(side=tk.LEFT)

# 해야할 업무 테이블 프레임
todo_table_frame = tk.Frame(todo_frame, bg="#F8F9FA")
todo_table_frame.pack(fill=tk.BOTH, expand=True)

# 해야할 업무 테이블 (중요 컬럼 포함)
todo_columns = ("중요", "해야할 업무", "등록일", "기한", "D-day")
todo_tree = ttk.Treeview(todo_table_frame, columns=todo_columns, show="headings", height=8, selectmode="extended")

# 정렬 상태 변수
sort_column = ""
sort_reverse = False

# 정렬 함수
def sort_todo_table(col):
    global sort_column, sort_reverse
    
    # 같은 컬럼 클릭 시 정렬 순서 반전
    if sort_column == col:
        sort_reverse = not sort_reverse
    else:
        sort_column = col
        sort_reverse = False
    
    # 모든 항목 가져오기
    items = []
    for child in todo_tree.get_children():
        item_data = todo_tree.item(child)
        tags = item_data.get('tags', [])
        

            
        values = list(item_data['values'])
        items.append((child, values, tags))
    
    # 중요 업무와 일반 업무 분리
    important_items = []
    normal_items = []
    
    for child, values, tags in items:
        # tags에서 todo_id 가져와서 중요 상태 확인
        todo_id = tags[0] if tags else None
        if todo_id and todo_id in todo_items and todo_items[todo_id].get("important", False):
            important_items.append((child, values, tags))
        else:
            normal_items.append((child, values, tags))
    
    # 일반 업무만 정렬 (중요 업무는 항상 상단 고정)
    if col == "등록일":
        normal_items.sort(key=lambda x: x[1][2], reverse=sort_reverse)  # 등록일 기준 (중요 컬럼 때문에 인덱스 +1)
    elif col == "기한":
        normal_items.sort(key=lambda x: x[1][3], reverse=sort_reverse)  # 기한 기준
    elif col == "D-day":
        # D-day 정렬을 위한 특별 처리
        def parse_dday(dday_text):
            if dday_text == "D-day":
                return 0
            elif dday_text.startswith("D-"):
                return int(dday_text[2:])
            elif dday_text.startswith("D+"):
                return -int(dday_text[2:])
            else:
                return 9999  # 날짜오류나 기타
        
        normal_items.sort(key=lambda x: parse_dday(x[1][4]), reverse=sort_reverse)  # D-day 기준
    
    # 기존 항목들 삭제
    for child, _, _ in items:
        todo_tree.delete(child)
    
    # 중요 업무를 맨 위에 먼저 추가 (상단 고정)
    for child, values, tags in important_items:
        todo_tree.insert("", "0", values=values, tags=tags)  # 맨 위에 삽입
    
    # 정렬된 일반 업무를 그 다음에 추가
    for child, values, tags in normal_items:
        todo_tree.insert("", "end", values=values, tags=tags)
    

    
    # 헤더에 정렬 표시 업데이트
    for c in todo_columns:
        if c == col:
            arrow = " ▼" if sort_reverse else " ▲"
            todo_tree.heading(c, text=c + arrow)
        else:
            todo_tree.heading(c, text=c)

# 중요 체크박스 토글 함수
def toggle_important(event):
    """중요 체크박스 더블클릭 이벤트"""
    try:
        region = todo_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = todo_tree.identify_column(event.x, event.y)
            if column == "#1":  # 중요 컬럼
                item = todo_tree.identify_row(event.y)
                if item:
                    current_values = list(todo_tree.item(item, 'values'))
                    tags = todo_tree.item(item, 'tags')
                    todo_id = tags[0] if tags else None
                    
                    if todo_id and todo_id in todo_items:
                        # 체크박스 상태 토글
                        if current_values[0] == "☐":
                            current_values[0] = "☑"
                            todo_items[todo_id]["important"] = True
                        else:
                            current_values[0] = "☐"
                            todo_items[todo_id]["important"] = False
                        
                        # 테이블 업데이트
                        todo_tree.item(item, values=current_values)
                        save_todo_settings()
                        
                        # 중요 상태 변경 시 테이블 재정렬
                        if sort_column:
                            sort_todo_table(sort_column)
                        else:
                            sort_todo_table("등록일")
    except Exception as e:
        print(f"중요 체크박스 토글 오류: {e}")

# 중요 표시 토글 함수 (우클릭 메뉴용)
def toggle_important_status():
    """선택된 항목의 중요 상태를 토글"""
    selected_items = todo_tree.selection()
    if not selected_items:
        return
    
    for item in selected_items:
        tags = todo_tree.item(item, 'tags')
        todo_id = tags[0] if tags else None
        
        if todo_id and todo_id in todo_items:
            # 중요 상태 토글
            current_important = todo_items[todo_id].get("important", False)
            todo_items[todo_id]["important"] = not current_important
            
            # ✅ 아이콘 표시 업데이트
            current_values = list(todo_tree.item(item, 'values'))
            current_values[0] = "✅" if not current_important else ""
            todo_tree.item(item, values=current_values)
    
    # 설정 저장
    save_todo_settings()
    
    # 테이블 재정렬
    if sort_column:
        sort_todo_table(sort_column)
    else:
        sort_todo_table("등록일")

# 헤더 설정
for col in todo_columns:
    if col in ["등록일", "기한", "D-day"]:
        # 정렬 가능한 컬럼에 클릭 이벤트 추가
        todo_tree.heading(col, text=col, anchor=tk.CENTER, command=lambda c=col: sort_todo_table(c))
    else:
        todo_tree.heading(col, text=col, anchor=tk.CENTER)
    
    if col == "중요":
        todo_tree.column(col, width=60, minwidth=50, anchor=tk.CENTER)
    elif col == "해야할 업무":
        todo_tree.column(col, width=200, minwidth=150, anchor=tk.W)
    elif col == "등록일":
        todo_tree.column(col, width=100, minwidth=80, anchor=tk.CENTER)
    elif col == "기한":
        todo_tree.column(col, width=120, minwidth=100, anchor=tk.CENTER)
    elif col == "D-day":
        todo_tree.column(col, width=80, minwidth=60, anchor=tk.CENTER)

# 해야할 업무 우클릭 메뉴
def show_todo_context_menu(event):
    """해야할 업무 테이블 우클릭 메뉴 표시"""
    # 클릭한 위치의 항목 선택
    item = todo_tree.identify_row(event.y)
    if item:
        todo_tree.selection_set(item)
        
        # 메뉴 생성
        context_menu = tk.Menu(root, tearoff=0)
        
        # 중요 표시 상태 확인
        tags = todo_tree.item(item, 'tags')
        todo_id = tags[0] if tags else None
        
        if todo_id and todo_id in todo_items:
            is_important = todo_items[todo_id].get("important", False)
            menu_text = "중요 표시 해제" if is_important else "중요 표시"
            context_menu.add_command(label=menu_text, command=toggle_important_status)
            context_menu.add_separator()
        
        context_menu.add_command(label="편집", command=lambda: edit_todo_item(todo_id))
        context_menu.add_command(label="삭제", command=lambda: delete_selected_todos())
        
        # 메뉴 표시
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

todo_tree.pack(side="left", fill=tk.BOTH, expand=True)

# 해야할 업무 테이블 스크롤바
todo_scrollbar = ttk.Scrollbar(todo_table_frame, orient="vertical", command=todo_tree.yview)
todo_tree.configure(yscrollcommand=todo_scrollbar.set)
todo_scrollbar.pack(side="right", fill="y")

# 해야할 업무 테이블 클릭 이벤트 (다중선택 지원)
def on_todo_click(event):
    """해야할 업무 클릭 이벤트 - 다중선택 지원"""
    # 다중선택은 Treeview에서 자동으로 처리됨 (selectmode="extended")
    pass

# Delete 키로 해야할 업무 삭제
def on_todo_delete_key(event):
    item = todo_tree.selection()
    if item:
        values = todo_tree.item(item, 'values')
        tags = todo_tree.item(item, 'tags')
        
        if tags:  # 등록 버튼이 아닌 경우
            todo_id = tags[0]
            delete_todo_item(todo_id)

def todo_double_click(event):
    """해야할 업무 더블클릭 시 위쪽 UI에 자동 입력"""
    item = todo_tree.selection()
    if item:
        values = todo_tree.item(item, 'values')
        tags = todo_tree.item(item, 'tags')
        
        if tags:  # 등록 버튼이 아닌 경우
            todo_id = tags[0]
            # 위쪽 UI에 자동 입력
            apply_todo_to_ui(todo_id)

# 우클릭 메뉴 - 중요 표시 포함
def show_todo_context_menu_fixed(event):
    """해야할 업무 테이블 우클릭 메뉴 표시 - 중요 표시 포함"""
    # 클릭한 위치의 항목 선택
    item = todo_tree.identify_row(event.y)
    if item:
        todo_tree.selection_set(item)
        
        # 메뉴 생성
        context_menu = tk.Menu(root, tearoff=0)
        
        # 중요 표시 상태 확인
        tags = todo_tree.item(item, 'tags')
        todo_id = tags[0] if tags else None
        
        if todo_id and todo_id in todo_items:
            is_important = todo_items[todo_id].get("important", False)
            menu_text = "중요 표시 해제" if is_important else "중요 표시"
            context_menu.add_command(label=menu_text, command=toggle_important_status)
            context_menu.add_separator()
        
        context_menu.add_command(label="편집", command=lambda: edit_todo_item(todo_id))
        context_menu.add_command(label="삭제", command=lambda: delete_selected_todos())
        context_menu.add_separator()
        context_menu.add_command(label="위쪽 UI에 입력", command=lambda: apply_todo_to_ui(todo_id))
        
        # 메뉴 표시
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

# 모든 이벤트 바인딩 완전 제거 후 새로 설정
todo_tree.unbind("<Double-1>")
todo_tree.unbind("<Button-1>")
todo_tree.unbind("<ButtonRelease-1>")
todo_tree.unbind("<Key>")
todo_tree.unbind("<KeyRelease>")
todo_tree.unbind("<<TreeviewSelect>>")
todo_tree.unbind("<Button-3>")

# 간소화된 이벤트 바인딩 설정
todo_tree.bind("<Button-1>", on_todo_click)  # 단일클릭
todo_tree.bind("<Double-1>", todo_double_click)  # 더블클릭으로 위쪽 UI에 입력
todo_tree.bind("<Delete>", on_todo_delete_key)  # Delete 키
todo_tree.bind("<Button-3>", show_todo_context_menu_fixed)  # 우클릭 메뉴

# 오른쪽 프레임 내용 (기존 로그 테이블)
log_frame = tk.Frame(right_frame)
log_frame.pack(fill=tk.BOTH, expand=True)

columns = ("날짜", "시작시간", "완료시간", "코드", "MK번호", "공정명", "업무 내용", "소요시간") # 칼럼 순서 변경
tree = ttk.Treeview(log_frame, columns=columns, show="headings", selectmode="extended")
for col in columns:
    tree.heading(col, text=col, anchor=tk.CENTER, command=lambda c=col: sort_treeview(c))
    if col == "업무 내용":
        tree.column(col, width=200, minwidth=150)
    elif col == "공정명":
        tree.column(col, width=180, minwidth=120)
    elif col == "소요시간":
        tree.column(col, width=100, minwidth=80, anchor=tk.CENTER)
    else:
        tree.column(col, anchor=tk.CENTER, width=90, minwidth=70)
tree.pack(side="left", fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

#   ====== 로그 관리 버튼들 =====
log_management_frame = tk.Frame(right_frame)
log_management_frame.pack(side="bottom", fill="x", pady=10)

# 로그 열기 버튼
open_log_button = tk.Button(log_management_frame, text="로그원본열기", command=open_log_file)
open_log_button.pack(side="left", padx=5)

# 로그불러오기(전체/오늘) 버튼
reload_log_button = tk.Button(log_management_frame, text="전체 기록보기", command=toggle_log_filter)
reload_log_button.pack(side="left", padx=5)

# 로그 추가 버튼
add_log_button = tk.Button(log_management_frame, text="로그 추가", command=lambda: add_log_entry(), bg="#4caf50", fg="white", width=12)
add_log_button.pack(side="left", padx=5)

# 로그 삭제 버튼
delete_log_button = tk.Button(log_management_frame, text="로그 삭제", command=lambda: delete_log_entry(), bg="#f44336", fg="white", width=12)
delete_log_button.pack(side="left", padx=5)

#   ====== 로그 내보내기 버튼 =====
def test_export_function():
    """엑셀 내보내기 함수"""
    export_to_excel_with_macro()

# 개발자 정보 라벨
developer_label = tk.Label(log_management_frame, text="개발자: 이재호", 
                          font=("Arial", 9, "bold"), fg="#666666", bg="#f0f0f0")
developer_label.pack(side="right", padx=(0, 10))

export_button = tk.Button(log_management_frame, text="엑셀로 저장", command=test_export_function, 
                         bg="#217346", fg="white", font=("Arial", 10), 
                         relief="raised", bd=2, padx=10, pady=2)
export_button.pack(side="right", padx=(0, 5))

# 테이블 더블 클릭 이벤트 바인딩 (헤더 제외)
def on_tree_double_click(event):
    # 클릭한 위치가 헤더인지 확인
    region = tree.identify("region", event.x, event.y)
    if region == "heading":
        return  # 헤더 클릭 시 아무것도 하지 않음
    
    # 헤더가 아닌 경우에만 로그 데이터를 UI에 자동 입력
    on_double_click(event)

tree.bind("<Double-1>", on_tree_double_click)

# 로그 테이블 우클릭 메뉴
def show_log_context_menu(event):
    # 클릭한 위치가 헤더인지 확인
    region = tree.identify("region", event.x, event.y)
    
    if region == "heading":
        # 헤더 우클릭: 카테고리 숨기기/보이기 메뉴
        show_header_context_menu(event)
    else:
        # 로그 항목 우클릭: 편집/삭제 메뉴
        show_item_context_menu(event)

def show_header_context_menu(event):
    """헤더 우클릭 메뉴"""
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="카테고리 숨기기", command=lambda: hide_category_column(event))
    menu.add_command(label="모든 카테고리 보이기", command=lambda: show_all_categories())
    menu.tk_popup(event.x_root, event.y_root)

def show_item_context_menu(event):
    """로그 항목 우클릭 메뉴"""
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="로그 편집", command=lambda: edit_log_entry())
    menu.add_command(label="로그 삭제", command=lambda: delete_log_entry())
    menu.tk_popup(event.x_root, event.y_root)

# 숨겨진 컬럼 추적
hidden_columns = set()

def hide_category_column(event):
    # 클릭한 위치가 헤더인지 확인
    region = tree.identify("region", event.x, event.y)
    if region != "heading":
        return
    
    # 클릭한 컬럼 확인
    column = tree.identify_column(event.x)
    column_name = tree.heading(column, "text")
    
    if column_name in ["날짜", "시작시간", "완료시간", "코드", "MK번호", "공정명", "업무 내용", "소요시간"]:
        # 컬럼 완전히 숨기기
        tree.column(column, width=0, minwidth=0, stretch=False)
        tree.heading(column, text="")  # 헤더 텍스트도 숨김
        hidden_columns.add(column_name)

def show_all_categories():
    """모든 카테고리 보이기"""
    columns = ["날짜", "시작시간", "완료시간", "코드", "MK번호", "공정명", "업무 내용", "소요시간"]
    for col in columns:
        if col in hidden_columns:
            # 컬럼을 다시 표시
            tree.column(col, stretch=True)  # stretch 복원
            tree.heading(col, text=col)  # 헤더 텍스트 복원
            
            # 기본 너비 설정
            if col == "업무 내용":
                tree.column(col, width=150, minwidth=100)
            elif col == "소요시간":
                tree.column(col, width=100, minwidth=80)
            else:
                tree.column(col, anchor=tk.CENTER, width=80, minwidth=60)
    hidden_columns.clear()

# 로그 편집 함수
def edit_log_entry():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("선택 오류", "편집할 로그를 선택해주세요.")
        return
    
    values = tree.item(selected_item, 'values')
    if not values:
        return
    
    dialog = tk.Toplevel(root)
    dialog.title("로그 편집")
    dialog.geometry("600x700")
    dialog.resizable(True, True)
    dialog.transient(root)
    dialog.grab_set()
    
    # ESC 키로 창 닫기
    def on_escape(event):
        dialog.destroy()
    
    dialog.bind("<Escape>", on_escape)
    
    # 창에 포커스 설정
    dialog.focus_set()
    
    # 메인 프레임
    main_frame = tk.Frame(dialog, bg="#f5f5f5")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # 제목
    title_label = tk.Label(main_frame, text="로그 편집", font=("Arial", 16, "bold"), bg="#f5f5f5", fg="#333333")
    title_label.pack(pady=(0, 20))
    
    # 입력 프레임
    input_frame = tk.Frame(main_frame, bg="#f5f5f5")
    input_frame.pack(fill="both", expand=True)
    
    # 날짜 섹션
    date_frame = tk.LabelFrame(input_frame, text="날짜", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    date_frame.pack(fill="x", pady=(0, 15))
    
    date_inner_frame = tk.Frame(date_frame, bg="#f5f5f5")
    date_inner_frame.pack()
    
    year_var = tk.StringVar(value=values[0][:4] if len(values) > 0 and values[0] else "")
    month_var = tk.StringVar(value=values[0][5:7] if len(values) > 0 and values[0] else "")
    day_var = tk.StringVar(value=values[0][8:10] if len(values) > 0 and values[0] else "")
    
    year_entry = tk.Entry(date_inner_frame, width=6, textvariable=year_var, font=("Arial", 11), relief="solid", bd=1)
    year_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="년", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    month_entry = tk.Entry(date_inner_frame, width=4, textvariable=month_var, font=("Arial", 11), relief="solid", bd=1)
    month_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="월", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    day_entry = tk.Entry(date_inner_frame, width=4, textvariable=day_var, font=("Arial", 11), relief="solid", bd=1)
    day_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(date_inner_frame, text="일", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 시간 섹션
    time_frame = tk.LabelFrame(input_frame, text="시간", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    time_frame.pack(fill="x", pady=(0, 15))
    
    # 시작시간
    start_time_frame = tk.Frame(time_frame, bg="#f5f5f5")
    start_time_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(start_time_frame, text="시작시간", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    start_time_str = values[1] if len(values) > 1 else ""
    sh_var = tk.StringVar(value=extract_num(start_time_str, 0))
    sm_var = tk.StringVar(value=extract_num(start_time_str, 1))
    
    sh_entry = tk.Entry(start_time_frame, width=4, textvariable=sh_var, font=("Arial", 11), relief="solid", bd=1)
    sh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(start_time_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    sm_entry = tk.Entry(start_time_frame, width=4, textvariable=sm_var, font=("Arial", 11), relief="solid", bd=1)
    sm_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(start_time_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 완료시간
    end_time_frame = tk.Frame(time_frame, bg="#f5f5f5")
    end_time_frame.pack(fill="x")
    
    tk.Label(end_time_frame, text="완료시간", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    end_time_str = values[2] if len(values) > 2 else ""
    eh_var = tk.StringVar(value=extract_num(end_time_str, 0))
    em_var = tk.StringVar(value=extract_num(end_time_str, 1))
    
    eh_entry = tk.Entry(end_time_frame, width=4, textvariable=eh_var, font=("Arial", 11), relief="solid", bd=1)
    eh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(end_time_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    em_entry = tk.Entry(end_time_frame, width=4, textvariable=em_var, font=("Arial", 11), relief="solid", bd=1)
    em_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(end_time_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 소요시간 (직접 편집 가능)
    duration_frame = tk.LabelFrame(input_frame, text="소요시간 (직접 편집)", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    duration_frame.pack(fill="x", pady=(0, 15))
    
    duration_inner_frame = tk.Frame(duration_frame, bg="#f5f5f5")
    duration_inner_frame.pack()
    
    duration_str = values[7] if len(values) > 7 else ""
    dh_var = tk.StringVar(value=extract_num(duration_str, 0))
    dm_var = tk.StringVar(value=extract_num(duration_str, 1))
    ds_var = tk.StringVar(value="0")  # 초는 기본값 0
    
    dh_entry = tk.Entry(duration_inner_frame, width=4, textvariable=dh_var, font=("Arial", 11), relief="solid", bd=1)
    dh_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="시", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    dm_entry = tk.Entry(duration_inner_frame, width=4, textvariable=dm_var, font=("Arial", 11), relief="solid", bd=1)
    dm_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="분", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT, padx=(0, 10))
    
    ds_entry = tk.Entry(duration_inner_frame, width=4, textvariable=ds_var, font=("Arial", 11), relief="solid", bd=1)
    ds_entry.pack(side=tk.LEFT, padx=(0, 5))
    tk.Label(duration_inner_frame, text="초", font=("Arial", 11), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # ESC 키로 창 닫기
    def on_escape(event):
        dialog.destroy()
    
    dialog.bind("<Escape>", on_escape)
    
    # 작업 정보 섹션
    work_frame = tk.LabelFrame(input_frame, text="작업 정보", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333333", padx=10, pady=10)
    work_frame.pack(fill="x", pady=(0, 15))
    
    # 작업코드
    code_frame = tk.Frame(work_frame, bg="#f5f5f5")
    code_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(code_frame, text="작업코드", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    code_var_edit = tk.StringVar(value=values[3] if len(values) > 3 else "")
    code_combo = ttk.Combobox(code_frame, textvariable=code_var_edit, values=["CAD", "KT", "ET", "KC", "TT"], width=15, state="readonly", font=("Arial", 11))
    code_combo.pack(side=tk.LEFT)
    
    # MK번호
    mk_frame = tk.Frame(work_frame, bg="#f5f5f5")
    mk_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(mk_frame, text="MK번호", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    mknum_var_edit = tk.StringVar(value=values[4] if len(values) > 4 else "")
    mk_entry_edit = tk.Entry(mk_frame, width=12, textvariable=mknum_var_edit, font=("Arial", 11), relief="solid", bd=1)
    mk_entry_edit.pack(side=tk.LEFT, padx=(0, 5))
    
    def set_mk_suffix_dialog(suffix):
        val = mk_entry_edit.get().strip()
        # 숫자 5자리만 있는지 확인 (M/T/R 문자가 있어도 허용)
        if re.match(r"^\d{5}[MTRmtr]?$", val):
            # 숫자 5자리 부분만 추출하고 새로운 suffix 추가
            number_part = val[:5]
            mk_entry_edit.delete(0, tk.END)
            mk_entry_edit.insert(0, number_part + suffix)
        elif val.isdigit() and len(val) == 5:
            # 숫자 5자리만 있는 경우
            mk_entry_edit.delete(0, tk.END)
            mk_entry_edit.insert(0, val + suffix)
    
    for suffix, btn_text in [("M", "M"), ("T", "T"), ("R", "R")]:
        btn = tk.Button(mk_frame, text=btn_text, width=2, command=lambda s=suffix: set_mk_suffix_dialog(s), 
                       font=("Arial", 10), relief="solid", bd=1, bg="#e0e0e0")
        btn.pack(side=tk.LEFT, padx=2)
    
    # 공정명
    category_frame = tk.Frame(work_frame, bg="#f5f5f5")
    category_frame.pack(fill="x", pady=(0, 10))
    
    tk.Label(category_frame, text="공정명", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    category_var_edit = tk.StringVar(value=values[5] if len(values) > 5 else "")
    category_combo = ttk.Combobox(category_frame, textvariable=category_var_edit, values=category_list, width=25, font=("Arial", 11))
    category_combo.pack(side=tk.LEFT)
    
    # 공정명 선택 시 작업코드 자동 연동
    def update_code_from_category_edit_dialog(event=None):
        selected_category = category_var_edit.get()
        print(f"편집창 공정명 선택됨: {selected_category}")  # 디버깅용
        if selected_category:
            # 기존 category_code_mapping 사용
            if selected_category in category_code_mapping:
                code_var_edit.set(category_code_mapping[selected_category])
                print(f"편집창 작업코드 설정됨: {category_code_mapping[selected_category]}")  # 디버깅용
            else:
                print(f"편집창 매핑되지 않은 공정명: {selected_category}")  # 디버깅용
    
    # 공정명 콤보박스에 이벤트 바인딩
    category_combo.bind("<<ComboboxSelected>>", update_code_from_category_edit_dialog)
    category_combo.bind("<KeyRelease>", update_code_from_category_edit_dialog)
    category_combo.bind("<FocusOut>", update_code_from_category_edit_dialog)
    
    # 업무내용
    task_frame = tk.Frame(work_frame, bg="#f5f5f5")
    task_frame.pack(fill="x")
    
    tk.Label(task_frame, text="업무내용", font=("Arial", 11), bg="#f5f5f5", width=10, anchor="w").pack(side=tk.LEFT)
    task_text_edit = tk.Text(task_frame, width=40, height=4, font=("Arial", 11), relief="solid", bd=1)
    task_text_edit.pack(side=tk.LEFT, fill="x", expand=True)
    if len(values) > 6:
        task_text_edit.insert("1.0", values[6])

    def save_edit():
        try:
            # MK번호 검증
            mk_number = mknum_var_edit.get().strip()
            code = code_var_edit.get().strip()
            
            if mk_number:  # MK번호가 입력된 경우에만 검증
                is_valid, error_msg = validate_mk_number(mk_number)
                if not is_valid:
                    messagebox.showwarning("MK번호 오류", error_msg)
                    return
            
            # 기존 항목 정보 저장
            old_values = tree.item(selected_item, 'values')
            
            date_str = f"{year_var.get()}-{month_var.get().zfill(2)}-{day_var.get().zfill(2)}"
            start_time_str = f"{sh_var.get().zfill(2)}시 {sm_var.get().zfill(2)}분"
            end_time_str = f"{eh_var.get().zfill(2)}시 {em_var.get().zfill(2)}분"
            duration_str = f"{dh_var.get().zfill(2)}시 {dm_var.get().zfill(2)}분 {ds_var.get().zfill(2)}초"
            new_values = (
                date_str,
                start_time_str,
                end_time_str,
                code_var_edit.get(),
                mknum_var_edit.get(),
                category_var_edit.get(),
                task_text_edit.get("1.0", tk.END).strip(),
                duration_str
            )
            tree.item(selected_item, values=new_values)
            
            # 실제 로그 파일에서 기존 항목 삭제 후 새 항목 추가
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as file:
                    log_lines = file.readlines()
                
                # 기존 항목 삭제
                new_log_lines = []
                i = 0
                while i < len(log_lines):
                    line = log_lines[i]
                    should_delete = False
                    
                    # 업무 종료 로그 패턴 확인
                    end_pattern = re.compile(
                        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 업무 종료 - 코드: ([^,]*?)(?:, MK번호: ([^,]*))?(?:, 작업분류: ([^,]*))?(?:, 작업: ([^,]*))? \(소요 시간: (\d+)시간 (\d+)분 (\d+)초\)"
                    )
                    
                    match = end_pattern.search(line)
                    if match:
                        end_date = match.group(1)[:10]
                        end_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").strftime("%H시%M분")
                        code = match.group(2)
                        mk_number = match.group(3) or ""
                        category = match.group(4) or ""
                        task = match.group(5) or ""
                        hours = match.group(6)
                        minutes = match.group(7)
                        seconds = match.group(8)
                        duration = f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초"
                        
                        # 기존 항목과 일치하는지 확인 (더 정확한 매칭)
                        old_end_time = old_values[2] if len(old_values) > 2 else ""
                        old_code = old_values[3] if len(old_values) > 3 else ""
                        old_mk_number = old_values[4] if len(old_values) > 4 else ""
                        old_category = old_values[5] if len(old_values) > 5 else ""
                        old_task = old_values[6] if len(old_values) > 6 else ""
                        old_duration = old_values[7] if len(old_values) > 7 else ""
                        
                        # 시간 형식 통일 (HH시 MM분 -> HH시MM분)
                        normalized_end_time = end_time.replace(" ", "")
                        normalized_old_end_time = old_end_time.replace(" ", "")
                        
                        if (old_values[0] == end_date and
                            normalized_old_end_time == normalized_end_time and
                            old_code == code and
                            old_mk_number == mk_number and
                            old_category == category and
                            old_task == task and
                            old_duration == duration):
                            should_delete = True
                            # 시작 로그도 함께 삭제
                            if i > 0 and "업무 시작" in log_lines[i-1]:
                                new_log_lines.pop()  # 시작 로그 제거
                    
                    if not should_delete:
                        new_log_lines.append(line)
                    i += 1
                
                # 새로운 로그 항목 추가
                start_datetime = f"{date_str} {sh_var.get().zfill(2)}:{sm_var.get().zfill(2)}:00"
                end_datetime = f"{date_str} {eh_var.get().zfill(2)}:{em_var.get().zfill(2)}:00"
                
                log_entry_start = f"[{start_datetime}] 업무 시작\n"
                log_entry_end = f"[{end_datetime}] 업무 종료 - 코드: {code_var_edit.get()}"
                
                if mknum_var_edit.get():
                    log_entry_end += f", MK번호: {mknum_var_edit.get()}"
                if category_var_edit.get():
                    log_entry_end += f", 작업분류: {category_var_edit.get()}"
                if task_text_edit.get("1.0", tk.END).strip():
                    log_entry_end += f", 작업: {task_text_edit.get('1.0', tk.END).strip()}"
                
                log_entry_end += f" (소요 시간: {dh_var.get()}시간 {dm_var.get()}분 {ds_var.get()}초)\n"
                
                # 새로운 로그 항목을 기존 항목이 있던 위치에 추가
                found_position = False
                for i, line in enumerate(new_log_lines):
                    if line.startswith(f"[{date_str}"):
                        # 같은 날짜의 로그들 사이에 새 로그 추가
                        new_log_lines.insert(i, log_entry_start)
                        new_log_lines.insert(i + 1, log_entry_end)
                        found_position = True
                        break
                
                if not found_position:
                    # 같은 날짜의 로그를 찾지 못했으면 맨 뒤에 추가
                    new_log_lines.append(log_entry_start)
                    new_log_lines.append(log_entry_end)
                
                # 새로운 로그 파일 저장
                with open(LOG_FILE, "w", encoding="utf-8") as file:
                    file.writelines(new_log_lines)
                
            except Exception as e:
                messagebox.showerror("오류", f"로그 파일 업데이트 실패: {str(e)}")
            
            # 시작시간 기준 자동 정렬
            all_items = [(tree.set(iid, '시작시간'), iid) for iid in tree.get_children()]
            all_items.sort(key=lambda x: x[0])
            for idx, (_, iid) in enumerate(all_items):
                tree.move(iid, '', idx)
            dialog.destroy()
            
            # 현재 정렬 상태 유지 (UI 새로고침 제거)
            if sort_column in column_sort_states:
                sort_treeview(sort_column)
        except Exception as e:
            messagebox.showerror("오류", f"로그 편집 실패: {e}")
    
    # 버튼 프레임
    button_frame = tk.Frame(main_frame, bg="#f5f5f5")
    button_frame.pack(pady=20)
    
    save_button = tk.Button(button_frame, text="저장", command=save_edit, 
                           bg="#4caf50", fg="white", font=("Arial", 12, "bold"), 
                           width=10, height=2, relief="flat")
    save_button.pack(side=tk.LEFT, padx=5)
    
    cancel_button = tk.Button(button_frame, text="취소", command=dialog.destroy,
                             bg="#f44336", fg="white", font=("Arial", 12, "bold"),
                             width=10, height=2, relief="flat")
    cancel_button.pack(side=tk.LEFT, padx=5)



# 우클릭 메뉴 바인딩
tree.bind("<Button-3>", show_log_context_menu)

# 초기 설정
reset_work()
load_logs() # 프로그램 시작 시 로그 로딩

# 기본 설정 불러오기 (즐겨찾기 설정 포함)
print("프로그램 시작 - 설정 불러오기 중...")
load_settings()
print(f"설정 불러오기 완료 - 즐겨찾기 {len(favorites)}개")

# 트레이 아이콘 초기화
tray_icon = None
if TRAY_AVAILABLE and pystray is not None:
    try:
        tray_icon = create_tray_icon()
        print("트레이 아이콘이 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"트레이 아이콘 초기화 실패: {e}")
        tray_icon = None

# 사용법 창 함수 (개발자가 자유롭게 작성)
def show_usage_guide():
    usage_window = tk.Toplevel(root)
    usage_window.title("사용법 가이드")
    usage_window.geometry("800x650")
    usage_window.resizable(True, True)
    usage_window.transient(root)
    
    # ESC 키로 창 닫기
    def on_escape(event):
        usage_window.destroy()
    
    usage_window.bind("<Escape>", on_escape)
    
    # 창에 포커스 설정
    usage_window.focus_set()
    
    # 메뉴바 추가
    menubar = tk.Menu(usage_window)
    usage_window.config(menu=menubar)
    
    # 파일 메뉴
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="파일", menu=file_menu)
    file_menu.add_command(label="저장", command=lambda: save_usage_content())
    file_menu.add_command(label="불러오기", command=lambda: load_usage_content())
    file_menu.add_separator()
    file_menu.add_command(label="닫기", command=usage_window.destroy)
    
    # 편집 메뉴
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="편집", menu=edit_menu)
    edit_menu.add_command(label="복사", command=lambda: usage_text.event_generate("<<Copy>>"))
    edit_menu.add_command(label="붙여넣기", command=lambda: usage_text.event_generate("<<Paste>>"))
    edit_menu.add_command(label="이미지 붙여넣기", command=lambda: paste_image_to_usage())
    
    # 스크롤 가능한 텍스트 위젯
    text_frame = tk.Frame(usage_window)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    global usage_text
    usage_text = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Arial", 11))
    usage_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=usage_text.yview)
    
    # 닫기 버튼 프레임
    button_frame = tk.Frame(usage_window)
    button_frame.pack(fill="x", padx=10, pady=(10, 10))
    
    # 닫기 버튼
    close_button = tk.Button(button_frame, text="닫기", command=usage_window.destroy, 
                            font=("Arial", 11), bg="#E0E0E0", fg="black", width=10, height=1)
    close_button.pack(side="right")
    
    # 기본 사용법 템플릿 (초등학생도 이해할 수 있도록 작성)
    default_content = """🎯 MK 업무기록 프로그램 v1.1 사용법 가이드 🎯
===============================================

안녕하세요! 이 프로그램은 업무를 기록하는 프로그램입니다.
마치 일기를 쓰듯이 업무를 기록할 수 있어요!

📝 기본 사용법 (매우 쉬워요!)

1️⃣ 프로그램 시작하기
   • MK 업무기록 프로그램 v1.1.exe 파일을 더블클릭하세요
   • 프로그램이 열리면 "업무 대기"라고 표시됩니다

2️⃣ 업무 시작하기
   • 왼쪽에 있는 정보들을 입력하세요:
     - MK번호: 예) 25001M (M, T, R 버튼으로 끝글자 바꾸기 가능)
     - 공정명: 드롭다운에서 선택하거나 직접 입력
     - 업무내용: 무엇을 했는지 간단히 적기
   • "START WORK" 버튼을 클릭하세요
   • 이제 "업무ing..."라고 표시되며 시간이 카운트됩니다!

3️⃣ 업무 종료하기
   • 업무가 끝나면 "END" 버튼을 클릭하세요
   • 자동으로 기록이 저장됩니다!

4️⃣ 기록 확인하기
   • 오른쪽 표에서 모든 기록을 볼 수 있어요
   • 더블클릭하면 해당 로그의 정보가 UI에 자동 입력됩니다!

📋 해야할 업무 관리 (v1.1 NEW!)
   • 아래쪽에 있는 "해야할 업무" 표를 확인하세요
   • "등록" 버튼을 클릭하면 새로운 업무를 추가할 수 있어요
   • 항목을 더블클릭하거나 우클릭하면 편집/삭제할 수 있어요
   • 중요 업무는 ✅ 표시로 최상단에 고정됩니다!

🔧 유용한 기능들

⭐ 즐겨찾기 버튼 (8개)
   • 자주 하는 업무를 즐겨찾기에 저장해두세요
   • 버튼을 우클릭하면 설정할 수 있어요
   • 클릭하면 자동으로 정보가 입력됩니다!

📋 로그 관리
   • "로그 추가" 버튼: 새로운 기록 추가
   • "로그 삭제" 버튼: 선택한 기록 삭제
   • 로그 더블클릭: 해당 로그 정보를 UI에 자동 입력

🔄 트레이 아이콘 기능
   • 프로그램을 최소화하면 시스템 트레이에 아이콘이 나타납니다
   • 트레이 아이콘을 클릭하면 프로그램이 다시 나타납니다
   • 우클릭 메뉴로 프로그램을 종료할 수 있습니다

📊 엑셀 내보내기
   • "엑셀로 저장" 버튼을 클릭하면 모든 기록을 엑셀 파일로 저장할 수 있습니다
   • 매크로가 포함된 엑셀 파일로 생성되어 추가 분석이 가능합니다

💡 해야할 업무 관리 팁
   • 중요 업무는 체크박스를 클릭하여 중요 표시를 할 수 있습니다
   • 중요 표시된 업무는 항상 리스트 최상단에 위치합니다
   • 날짜를 설정하여 기한을 관리할 수 있습니다
   • D-day 기능으로 남은 기간을 확인할 수 있습니다
   • "로그 편집" 버튼: 선택한 기록 수정
   • "로그 삭제" 버튼: 선택한 기록 삭제

📊 엑셀로 내보내기
   • "엑셀로 내보내기" 버튼을 클릭하면
   • 엑셀 파일로 저장할 수 있어요!

🔍 필터링
   • "전체/오늘" 버튼으로 오늘 기록만 볼 수 있어요

⌨️ 단축키
   • Ctrl+V: 클립보드에서 업무내용 붙여넣기
   • ESC: 창 닫기
   • F1: 이 사용법 보기
   • F2: 프로그램 기능 설명 보기

🖥️ 트레이 아이콘 기능
   • 창을 닫으면 트레이로 이동해요
   • 트레이 아이콘을 더블클릭하면 창이 다시 열려요
   • 우클릭하면 "열기" 또는 "종료"를 선택할 수 있어요

💡 사용 팁

1. 업무 시작 전에 미리 정보를 입력해두세요
2. 즐겨찾기를 활용하면 반복 업무가 편해요
3. 해야할 업무를 등록해서 업무 관리를 체계적으로 하세요
4. 중요 업무는 ✅ 표시로 우선순위를 관리하세요
5. 정기적으로 엑셀로 내보내서 백업하세요
6. 업무가 끝나면 꼭 END 버튼을 누르세요!

📋 해야할 업무 관리 팁

• 등록: "등록" 버튼 → MK번호, 공정명, 기한, 업무내용 입력
• 편집: 항목 더블클릭 또는 우클릭 → "편집"
• 삭제: 우클릭 → "삭제" 또는 Delete 키
• 중요 표시: 우클릭 → "중요 표시/해제"
• 기한 설정: 날짜선택 버튼으로 캘린더에서 선택
• D-day 확인: 기한이 지나면 D+, 오늘은 D-day, 앞으로는 D-로 표시

❓ 문제가 생기면?
   • 프로그램을 다시 시작해보세요
   • work_log.log 파일이 있는지 확인하세요
   • 개발자(이재호 사원)에게 문의하세요

이제 업무 기록을 시작해보세요! 🚀
"""
    
    usage_text.insert("1.0", default_content)
    
    def save_usage_content():
        try:
            content = usage_text.get("1.0", tk.END)
            with open("usage_guide.txt", "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("저장 완료", "사용법 가이드가 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"저장 중 오류가 발생했습니다: {e}")
    
    def load_usage_content():
        try:
            with open("usage_guide.txt", "r", encoding="utf-8") as f:
                content = f.read()
            usage_text.delete("1.0", tk.END)
            usage_text.insert("1.0", content)
            messagebox.showinfo("불러오기 완료", "사용법 가이드를 불러왔습니다.")
        except FileNotFoundError:
            messagebox.showinfo("알림", "저장된 사용법 가이드 파일이 없습니다.")
        except Exception as e:
            messagebox.showerror("불러오기 실패", f"불러오기 중 오류가 발생했습니다: {e}")
    
    def paste_image_to_usage():
        try:
            # 클립보드에서 이미지 가져오기
            image = ImageGrab.grabclipboard()
            if image:
                # 이미지 크기 조정 (너무 크면 축소)
                max_width = 600
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_width = int(image.width * ratio)
                    new_height = int(image.height * ratio)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Tkinter에서 사용할 수 있도록 변환
                img_tk = ImageTk.PhotoImage(image)
                
                # 텍스트에 이미지 삽입
                usage_text.image_create(tk.END, image=img_tk)
                usage_text.insert(tk.END, "\n")  # 이미지 뒤에 줄바꿈
                
                # 이미지 참조 유지
                if not hasattr(usage_text, "image_refs"):
                    usage_text.image_refs = []
                usage_text.image_refs.append(img_tk)
                
                messagebox.showinfo("성공", "이미지가 삽입되었습니다.")
            else:
                messagebox.showwarning("경고", "클립보드에 이미지가 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 삽입 중 오류가 발생했습니다: {e}")

# 업데이트 로그 창 함수 (프로그램 기능 상세 설명)
def show_update_log():
    update_window = tk.Toplevel(root)
    update_window.title("프로그램 기능 및 업데이트 로그")
    update_window.geometry("800x650")
    update_window.resizable(True, True)
    update_window.transient(root)
    
    # ESC 키로 창 닫기
    def on_escape(event):
        update_window.destroy()
    
    update_window.bind("<Escape>", on_escape)
    
    # 창에 포커스 설정
    update_window.focus_set()
    
    # 스크롤 가능한 텍스트 위젯
    text_frame = tk.Frame(update_window)
    text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    update_text = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Arial", 11))
    update_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=update_text.yview)
    
    # 닫기 버튼 프레임
    button_frame = tk.Frame(update_window)
    button_frame.pack(fill="x", padx=10, pady=(10, 10))
    
    # 닫기 버튼
    close_button = tk.Button(button_frame, text="닫기", command=update_window.destroy, 
                            font=("Arial", 11), bg="#E0E0E0", fg="black", width=10, height=1)
    close_button.pack(side="right")
    
    # 업데이트 로그 내용 (초등학생도 이해할 수 있도록 작성)
    update_content = """🚀 MK 업무기록 프로그램 v1.1 - 프로그램 기능 설명 🚀
===============================================

안녕하세요! 이 프로그램은 업무를 기록하는 프로그램입니다.
마치 일기를 쓰듯이 업무를 기록할 수 있어요!

📅 버전 1.1 (2025-10-04) - 로그 편집 기능 개선 🆕
========================================================

🎯 새로운 기능들 (v1.1의 핵심 기능!)

🔄 로그 더블클릭 편집 기능 (NEW!) ⭐
   • 로그 테이블에서 항목을 더블클릭하면 바로 편집 창이 열립니다
   • 빠른 수정이 가능하여 업무 효율성이 크게 향상됩니다
   • 기존: 우클릭 → 편집 클릭 (2단계)
   • 개선: 더블클릭 한 번으로 즉시 편집 (1단계)

📋 해야할 업무 관리 시스템 ⭐
   • 등록/편집/삭제 완전 지원
   • MK번호 + 공정명 + 업무내용 조합으로 표시
   • 기한 설정 및 D-day 자동 계산
   • 중요 표시로 최상단 고정 배치
   • 우클릭 메뉴로 편집/삭제/중요 표시
   • 다중선택 후 Delete 키로 일괄 삭제

⭐ 중요 표시 시스템 (NEW!)
   • ✅ 아이콘으로 중요 업무 표시
   • 중요 업무는 무조건 리스트 최상단 배치
   • 우클릭 메뉴에서 "중요 표시/해제" 선택
   • 시각적 구분으로 업무 우선순위 관리

🖥️ 트레이 아이콘 기능 개선
   • 더블클릭으로만 프로그램 창 열기 (오작동 방지)
   • 0.5초 이내 더블클릭 감지 로직
   • 우클릭 메뉴: 열기/종료 선택
   • 시스템 트레이에서 백그라운드 실행

🎨 UI/UX 개선
   • 해야할 업무 등록/편집 창 통일된 디자인
   • 창 크기 최적화로 깔끔한 인터페이스
   • 버튼 배치 및 여백 최적화
   • 전체적인 디자인 통일성 향상

🔧 기술적 개선
   • 날짜선택 중복 방지 기능
   • 공정명-작업구분 자동 연계
   • 오류 처리 강화
   • 메모리 사용량 최적화

📊 엑셀 내보내기 완전 개선 ⭐
   • 파일명 자동 설정: 전체 기록은 "업무기록(ALL)", 오늘 기록은 "업무기록(TODAY)"
   • 열 너비 최적화: 날짜/시간은 15, 코드는 10, 공정명/내용은 30

🔄 로그 더블클릭 자동 입력 기능 (NEW!)
   • 로그 리스트에서 항목을 더블클릭하면 해당 로그의 정보가 UI에 자동 입력됩니다
   • MK번호, 작업코드, 공정명, 업무내용이 자동으로 입력되어 재사용이 편리합니다
   • 이전 업무를 쉽게 재시작할 수 있어 업무 효율성이 크게 향상됩니다
   • 필터 기능 자동 적용: 모든 컬럼에 드롭다운 필터 추가
   • 누적시간 컬럼 추가: 일별 업무 소요시간 누적 표시
   • 소요시간 분 단위 정수 표시: "2시간 30분" → "150분"
   • 정렬 개선: 헤더는 가운데 굵은 글씨, 데이터는 컬럼별 최적 정렬
   • 엑셀 파일 자동 열기: 저장 후 바로 엑셀에서 확인 가능

🎯 기존 주요 기능들

1️⃣ 실시간 시간 카운터 ⏰
   • START 버튼을 누르면 시간이 실시간으로 카운트됩니다
   • "5분 30초" 이런 식으로 표시됩니다
   • END 버튼을 누르면 자동으로 멈춥니다

2️⃣ MK번호 관리 📝
   • CAD, ET, KT 작업: MK번호를 꼭 입력해야 해요 (예: 25001M)
   • KC, TT 작업: MK번호는 자유롭게 입력할 수 있어요
   • 소문자로 입력해도 자동으로 대문자로 바뀝니다 (m→M, t→T, r→R)

3️⃣ 기록 관리 시스템 📋
   • 기록을 더블클릭하면 수정할 수 있어요
   • 새로운 기록 추가, 기존 기록 삭제 가능
   • 엑셀 파일로 내보내서 백업할 수 있어요 (개선됨!)
   • 시작시간 순서대로 자동 정렬됩니다

4️⃣ 즐겨찾기 기능 ⭐
   • 자주 하는 업무를 8개까지 저장할 수 있어요
   • 버튼을 우클릭하면 설정할 수 있어요
   • 버튼을 클릭하면 자동으로 정보가 입력됩니다

5️⃣ 단축키 기능 ⌨️
   • 버튼을 우클릭하면 단축키를 설정할 수 있어요
   • 버튼에 단축키가 표시됩니다 (예: "START (F1)")
   • ESC 키로 창을 닫을 수 있어요

🔧 상세 기능 설명

📝 업무 시작/종료
   • START: 업무를 시작하고 시간을 카운트합니다
   • END: 업무를 종료하고 기록을 저장합니다
   • START를 두 번 누르면 자동으로 END가 됩니다

📋 해야할 업무 관리 (v1.1 개선!)
   • 등록: "등록" 버튼 클릭 → 해야할 업무 등록 창
   • 편집: 항목 더블클릭 또는 우클릭 → "편집"
   • 삭제: 우클릭 → "삭제" 또는 Delete 키
   • 중요 표시: 우클릭 → "중요 표시/해제"
   • 기한 설정: 날짜선택 버튼으로 캘린더에서 선택
   • D-day 자동 계산 및 표시

📝 기록 편집하기
   • 날짜: 년/월/일을 따로 입력할 수 있어요
   • 시작/완료시간: 시/분을 따로 입력할 수 있어요
   • 소요시간: 시/분/초를 따로 입력할 수 있어요
   • 작업코드: CAD/KT/ET/KC/TT 중에서 선택
   • MK번호: 직접 입력하거나 M/T/R 버튼 사용
   • 공정명: 목록에서 선택하거나 직접 입력
   • 업무내용: 자유롭게 텍스트 입력

📊 엑셀로 내보내기 (개선됨!)
   • 파일명: 업무기록(ALL/TODAY)_YYMMDD.xlsx
   • 열 너비 최적화: 날짜/시간 15, 코드 10, 공정명/내용 30
   • 필터 기능: 모든 컬럼에 드롭다운 필터 자동 적용
   • 누적시간: 일별 업무 소요시간 누적 표시
   • 소요시간: 분 단위 정수로 표시 (예: 150분)
   • 정렬: 헤더 가운데 굵은 글씨, 데이터 컬럼별 최적 정렬
   • 자동 열기: 저장 후 엑셀 파일 자동 열기

⏰ 실시간 기능
   • 현재시간이 1초마다 업데이트됩니다
   • 작업 소요시간이 실시간으로 카운트됩니다
   • 상태가 "업무 대기" ↔ "업무ing..."로 바뀝니다

🖥️ 화면 구성

📱 메인 화면
   • 왼쪽: 정보 입력하는 곳
   • 오른쪽: 기록을 보는 표
   • 위쪽: 현재시간과 도움말 버튼
   • 아래쪽: 해야할 업무 관리 (v2.0 NEW!)

🔘 버튼들
   • RESET: 모든 정보를 초기화
   • START WORK: 업무 시작
   • 실시간 소요시간 표시
   • MK번호 입력 + M/T/R 버튼
   • 공정명 선택 + 코드 자동 생성

📋 기록 표
   • 컬럼: 날짜, 시작시간, 완료시간, 코드, MK번호, 공정명, 업무내용, 소요시간
   • 여러 개를 한 번에 선택할 수 있어요
   • 우클릭하면 메뉴가 나와요

📋 해야할 업무 표 (v2.0 NEW!)
   • 컬럼: 중요표시, 업무내용, 등록일, 기한, D-day
   • 중요 업무는 ✅ 표시로 최상단 고정
   • 기한이 지난 업무는 D+로 표시
   • 오늘 마감 업무는 D-day로 표시
   • 앞으로 남은 업무는 D-로 표시

🔮 앞으로 업데이트 예정
• 버전 2.2: 더 많은 개선사항 추가 예정
• 버전 3.0: 완전히 새로운 버전 예정

💬 문의사항
개발자(이재호 사원)에게 개선사항이나 문제점을 알려주시면
다음 업데이트에 반영하겠습니다!

이제 업무 기록을 시작해보세요! 🚀
"""
    
    update_text.insert("1.0", update_content)
    update_text.config(state="disabled")  # 읽기 전용

# 공지사항 버튼들
notice_frame = tk.Frame(left_frame)
notice_frame.grid(row=0, column=2, padx=5, pady=5, sticky="w")

usage_button = tk.Button(notice_frame, text="사용법", command=show_usage_guide, 
                        bg="#E0E0E0", fg="black", width=8, height=1)
usage_button.pack(side=tk.LEFT, padx=2)

update_button = tk.Button(notice_frame, text="업데이트 v1.1", command=show_update_log, 
                         bg="#E0E0E0", fg="black", width=12, height=1)
update_button.pack(side=tk.LEFT, padx=2)

# 로그 삭제 함수
def delete_log_entry():
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("선택 오류", "삭제할 로그를 선택해주세요.")
        return
    count = len(selected_items)
    if count == 1:
        result = messagebox.askyesno("삭제 확인", "선택한 로그를 삭제하시겠습니까?")
    else:
        result = messagebox.askyesno("삭제 확인", f"선택한 {count}개의 로그를 삭제하시겠습니까?")
    if result:
        try:
            # 삭제할 항목들의 정보 수집
            items_to_delete = []
            for item in selected_items:
                values = tree.item(item, 'values')
                if values:
                    date = values[0]
                    start_time = values[1]
                    end_time = values[2]
                    code = values[3]
                    mk_number = values[4]
                    category = values[5]
                    task = values[6]
                    duration = values[7]
                    
                    items_to_delete.append({
                        'date': date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'code': code,
                        'mk_number': mk_number,
                        'category': category,
                        'task': task,
                        'duration': duration
                    })
            
            # 로그 파일 읽기
            with open(LOG_FILE, "r", encoding="utf-8") as file:
                log_lines = file.readlines()
            
            # 새로운 로그 파일 생성 (삭제할 항목 제외)
            new_log_lines = []
            deleted_count = 0
            i = 0
            
            while i < len(log_lines):
                line = log_lines[i]
                should_delete = False
                
                # 업무 종료 로그 패턴 확인
                end_pattern = re.compile(
                    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 업무 종료 - 코드: ([^,]+)(?:, MK번호: ([^,]*))?(?:, 작업분류: ([^,]*))?(?:, 작업: ([^,]*))? \(소요 시간: (\d+)시간 (\d+)분 (\d+)초\)"
                )
                
                match = end_pattern.search(line)
                if match:
                    end_date = match.group(1)[:10]
                    end_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").strftime("%H시 %M분")
                    code = match.group(2)
                    mk_number = match.group(3) or ""
                    category = match.group(4) or ""
                    task = match.group(5) or ""
                    hours = match.group(6)
                    minutes = match.group(7)
                    seconds = match.group(8)
                    duration = f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초"
                    
                    # 삭제할 항목과 일치하는지 확인
                    for delete_item in items_to_delete:
                        if (delete_item['date'] == end_date and
                            delete_item['end_time'] == end_time and
                            delete_item['code'] == code and
                            delete_item['mk_number'] == mk_number and
                            delete_item['category'] == category and
                            delete_item['task'] == task and
                            delete_item['duration'] == duration):
                            should_delete = True
                            deleted_count += 1
                            # 시작 로그도 함께 삭제
                            if i > 0 and "업무 시작" in log_lines[i-1]:
                                new_log_lines.pop()  # 시작 로그 제거
                            break
                
                if not should_delete:
                    new_log_lines.append(line)
                i += 1
            
            # 새로운 로그 파일 저장 (오늘기록 보기에서도 원본 파일에 반영)
            with open(LOG_FILE, "w", encoding="utf-8") as file:
                file.writelines(new_log_lines)
            
            # UI에서도 삭제
            for item in selected_items:
                tree.delete(item)
            
            # 현재 정렬 상태 유지
            if sort_column in column_sort_states:
                sort_treeview(sort_column)
            
        except Exception as e:
            messagebox.showerror("오류", f"로그 파일 삭제 중 오류가 발생했습니다: {str(e)}")

# 중복 실행 체크
if not check_single_instance():
    sys.exit()

# 초기 로그 로딩
load_logs()

# 프로그램 종료 시 설정 저장
root.protocol("WM_DELETE_WINDOW", on_closing)

# 프로그램 실행
root.mainloop()