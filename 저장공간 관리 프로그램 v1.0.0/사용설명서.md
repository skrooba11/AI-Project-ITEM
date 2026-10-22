# 저장공간 관리 프로그램 - 실행 환경 요구사항

## 1. 요약

- **외부 라이브러리 설치가 필요 없습니다.** `CODE.py`는 파이썬 표준 라이브러리만 사용합니다.
- 따라서 `pip install` 할 것이 없으며, **Python만 올바르게 설치되어 있으면 바로 실행**됩니다.

## 2. 필수 환경

| 항목 | 요구사항 | 비고 |
|---|---|---|
| OS | Windows 10 / 11 (권장) | 드라이브 목록·볼륨 이름 조회, DPI 설정에 Windows API(`ctypes.windll`) 사용. macOS/Linux에서는 일부 기능이 동작하지 않을 수 있음 |
| Python | 3.8 이상 (개발 환경: **3.13.1**) | |
| tkinter (Tcl/Tk) | Python 설치 시 함께 설치 | GUI에 필요. 아래 설치 방법 참고 |
| 폰트 | 맑은 고딕 | Windows 기본 폰트 (별도 설치 불필요) |

## 3. 사용하는 라이브러리 (모두 표준 라이브러리)

| 모듈 | 용도 |
|---|---|
| `tkinter` (`ttk`, `messagebox`, `filedialog`, `font`) | GUI |
| `os`, `sys`, `shutil`, `pathlib` | 파일/폴더 처리, 디스크 용량 조회 |
| `hashlib` | 중복 파일 검사 (해시 비교) |
| `json` | 설정/데이터 저장 |
| `datetime`, `time` | 날짜·시간 처리 |
| `collections` (`defaultdict`) | 파일 분류 집계 |
| `threading` | 백그라운드 분석 |
| `re`, `string` | 문자열 처리, 드라이브 문자 목록 |
| `platform`, `ctypes` | OS 확인, Windows API 호출 |
| `webbrowser` | 링크 열기 |

## 4. 새 컴퓨터에서 설치 및 실행 방법

### 4-1. Python 설치
1. https://www.python.org/downloads/ 에서 Python 3.13 (또는 3.8 이상)을 내려받습니다.
2. 설치할 때:
   - **"Add python.exe to PATH"** 에 체크합니다.
   - "Customize installation"을 선택한 경우 **"tcl/tk and IDLE"** 항목이 체크되어 있는지 확인합니다 (tkinter에 필요, 기본값은 체크됨).

### 4-2. 설치 확인
명령 프롬프트(cmd) 또는 PowerShell에서 실행합니다.

```bash
python --version
python -m tkinter
```

`python -m tkinter`를 실행했을 때 작은 테스트 창이 뜨면 정상입니다.

### 4-3. 프로그램 실행
`CODE.py`가 있는 폴더에서 실행합니다.

```bash
python CODE.py
```

> 가상환경(`.venv`)은 필요 없습니다. 외부 패키지가 없으므로 시스템 Python으로 바로 실행할 수 있습니다.

## 5. (선택) exe 파일로 빌드하기

Python이 설치되지 않은 컴퓨터에 배포하려면 PyInstaller로 exe를 만들 수 있습니다. **이 경우에만** 외부 패키지가 필요합니다.

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico CODE.py
```

빌드된 파일은 `dist` 폴더에 생성됩니다.
