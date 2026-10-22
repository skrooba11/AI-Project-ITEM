# SL 웹서버 QCS 승인원 자동화 – 실행 환경 및 설치 안내

대상 스크립트: `SL 웹서버 QCS 승인원 자동화_최종.py`

---

## 1. 필수 환경 (라이브러리 외)

| 항목 | 요구사항 | 비고 |
|---|---|---|
| 운영체제 | **Windows** | `os.startfile`, Excel COM 제어를 사용하므로 Windows 전용 |
| Microsoft Excel | **설치 필수** (데스크톱 버전) | xlwings가 실제 Excel 프로그램을 백그라운드로 실행하여 작업함 |
| Python | 3.10 이상 권장 (현재 PC: 3.13에서 동작 확인) | 설치 시 **"Add Python to PATH"** 와 **"tcl/tk and IDLE"** 옵션 체크 |

> Python 다운로드: https://www.python.org/downloads/windows/

---

## 2. 사용 라이브러리 목록

### 2-1. 별도 설치가 필요한 라이브러리

| 라이브러리 (import 이름) | pip 설치 이름 | 현재 PC 버전 | 용도 |
|---|---|---|---|
| `xlwings` | `xlwings` | 0.33.12 | 엑셀 파일 열기, 이미지 삽입, 시트 복사 |
| `PIL` | `pillow` | 11.1.0 | 이미지 파일 열기 및 PNG 변환 |
| (xlwings 의존성) | `pywin32` | 310 | xlwings가 Excel을 제어할 때 사용 (xlwings 설치 시 자동 설치됨) |

### 2-2. Python 기본 내장 라이브러리 (설치 불필요)

| 라이브러리 | 용도 |
|---|---|
| `os` | 폴더 열기, 경로 처리 |
| `shutil` | 파일 복사, 임시 폴더 삭제 |
| `tkinter` | 파일 선택 / 저장 대화상자, 메시지박스 |
| `pathlib` | 경로 처리 |
| `traceback` | 오류 내용 출력 |

> `tkinter`는 Python 기본 설치에 포함되어 있습니다. 만약 `ModuleNotFoundError: No module named 'tkinter'` 오류가 나면 Python 설치 프로그램을 다시 실행 → **Modify** → **"tcl/tk and IDLE"** 체크 후 설치하세요.

---

## 3. 설치 명령어 (터미널에 입력)

PowerShell 또는 명령 프롬프트(cmd)를 열고 아래 명령어를 입력합니다.

### 방법 A. 바로 설치 (가장 간단)

```powershell
python -m pip install --upgrade pip
python -m pip install xlwings pillow
```

### 방법 B. 현재 PC와 동일한 버전으로 설치 (버전 차이로 인한 오류 방지)

```powershell
python -m pip install xlwings==0.33.12 pillow==11.1.0 pywin32==310
```

### 방법 C. 가상환경(.venv)을 만들어 설치 (다른 프로젝트와 분리하고 싶을 때)

스크립트가 있는 `CODE` 폴더에서 실행:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install xlwings pillow
```

> PowerShell에서 `Activate.ps1` 실행 시 "스크립트를 실행할 수 없습니다" 오류가 나면 아래 명령어를 먼저 한 번 입력하세요.
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> 명령 프롬프트(cmd)를 사용하는 경우에는 `.\.venv\Scripts\activate.bat` 으로 활성화합니다.

---

## 4. 설치 확인

```powershell
python -c "import xlwings, PIL, tkinter; print('xlwings', xlwings.__version__); print('pillow', PIL.__version__); print('OK')"
```

`OK`가 출력되면 설치가 정상적으로 완료된 것입니다.

---

## 5. 실행 방법

스크립트가 있는 `CODE` 폴더에서:

```powershell
python "SL 웹서버 QCS 승인원 자동화_최종.py"
```

실행하면 파일 선택 창이 순서대로 나타납니다.

1. 승인원 엑셀 파일 (.xlsx)
2. 금형 명판사진 (여러 장 선택 가능) → 3번째 시트 D4
3. 핫런너 명판사진 → 3번째 시트 D31
4. 금형 열린사진 → 4번째 시트 D4
5. 금형 닫힌사진 → 4번째 시트 D31
6. 전극사진 → 5번째 시트 D4 (4장씩 가로 배치)
7. 금형자재표 엑셀 파일 → 6번째 시트에 전체 복사
8. 결과 파일 저장 위치 및 파일명 지정

사진/자재표는 선택하지 않고 취소해도 해당 항목만 건너뛰고 진행됩니다.

---

## 6. 주의사항

- 승인원 엑셀 파일에는 **시트가 최소 6개** 있어야 합니다 (3~6번째 시트에 작업).
- 실행 전 **열려 있는 Excel 창은 저장 후 닫아두는 것**을 권장합니다 (백그라운드 Excel과 충돌 방지).
- 실행 중 현재 폴더에 `temp_img` 임시 폴더가 생성되며, 작업이 끝나면 자동 삭제됩니다.
- 오류 발생 시 백그라운드에 Excel 프로세스가 남아 있을 수 있습니다. 작업 관리자에서 `EXCEL.EXE`를 종료한 후 다시 실행하세요.
