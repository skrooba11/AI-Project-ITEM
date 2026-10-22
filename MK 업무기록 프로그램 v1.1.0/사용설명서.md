# MK 업무기록 프로그램 v1.1 - 실행 환경 및 필요 라이브러리

## 1. 실행 환경

| 항목 | 내용 |
|------|------|
| 운영체제 | Windows 10 / 11 (화면 캡처·트레이 기능이 Windows 기준으로 작성됨) |
| Python | 3.10 이상 권장 (개발 환경: Python 3.10.10) |
| tkinter | Python 공식 설치 파일에 기본 포함 (설치 시 "tcl/tk and IDLE" 옵션이 체크되어 있어야 함) |

## 2. 설치가 필요한 외부 라이브러리

| 패키지 (pip 이름) | 코드에서 import | 개발 환경 버전 | 용도 | 필수 여부 |
|------|------|------|------|------|
| `pillow` | `from PIL import ...` | 11.2.1 | 화면 캡처(ImageGrab), 이미지 처리, 트레이 아이콘 | 필수 |
| `pyperclip` | `import pyperclip` | 1.9.0 | 클립보드 복사/붙여넣기 | 필수 |
| `openpyxl` | `import openpyxl` | 3.1.5 | 엑셀 파일 읽기/쓰기, 서식 지정 | 필수 |
| `pandas` | `import pandas as pd` | 2.3.1 | 업무기록 데이터 처리 및 엑셀 내보내기 | 필수 |
| `tkcalendar` | `from tkcalendar import Calendar` | 1.6.1 | 날짜 선택 캘린더 위젯 | 필수 (없으면 실행 시 자동 설치 시도) |
| `pystray` | `import pystray` | 0.19.5 | 시스템 트레이 아이콘 기능 | 선택 (없으면 트레이 기능만 비활성화) |

> `numpy`(pandas 의존), `babel`(tkcalendar 의존) 등은 위 패키지 설치 시 자동으로 함께 설치됩니다.

## 3. 표준 라이브러리 (별도 설치 불필요)

`tkinter`, `datetime`, `os`, `shutil`, `re`, `sys`, `json`, `threading`, `time`, `subprocess`, `socket`, `traceback`

## 4. 설치 방법

다른 컴퓨터에서는 아래 한 줄이면 설치됩니다. 명령 프롬프트(cmd) 또는 PowerShell에서 실행하세요.

```bash
pip install pillow pyperclip openpyxl pandas tkcalendar pystray
```

개발 환경과 동일한 버전으로 맞추려면:

```bash
pip install pillow==11.2.1 pyperclip==1.9.0 openpyxl==3.1.5 pandas==2.3.1 tkcalendar==1.6.1 pystray==0.19.5
```

## 5. 실행 방법

```bash
python "MK 업무기록 프로그램 v1.1_최종코드.py"
```

## 6. 참고 사항

- 프로그램은 실행 폴더의 `settings.json`(설정)과 `work_log.log`(로그)를 사용합니다. 다른 컴퓨터로 옮길 때 기존 설정을 유지하려면 `settings.json`도 함께 복사하세요.
- 중복 실행 방지를 위해 로컬 소켓 포트를 사용하므로, 프로그램이 이미 실행 중이면 새로 실행되지 않습니다.
- Python 설치 없이 사용하려면 같은 폴더의 `MK 업무기록 프로그램 v1.1.exe`를 실행하면 됩니다.
