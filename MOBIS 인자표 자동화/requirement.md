# MOBIS 인자표 자동화 - 실행 환경 및 필요 라이브러리

대상 코드: `MOBIS 인자표 자동화_최종.py`

인자표 엑셀 파일(.xlsx)에 전극사진, 금형사진, 제품사진을 자동으로 넣고 `_updated` 파일로 저장하는 프로그램입니다.

---

## 1. 실행 환경 (프로그램)

| 항목 | 조건 | 비고 |
|------|------|------|
| 운영체제 | **Windows** | `os.startfile`(탐색기 열기)이 Windows 전용 기능이라 Mac/Linux에서는 실행되지 않습니다. |
| Microsoft Excel | **설치 필수** | xlwings가 실제 Excel 프로그램을 백그라운드로 실행해서 작업합니다. Excel이 없으면 동작하지 않습니다. |
| Python | **3.9 이상** (현재 개발 PC: 3.13.1) | 설치 시 **"Add python.exe to PATH"** 항목을 꼭 체크하세요. 이 항목을 체크해야 터미널에서 `python`, `pip` 명령을 쓸 수 있습니다. |

Python 다운로드: https://www.python.org/downloads/

---

## 2. 필요 라이브러리

### 2-1. 따로 설치해야 하는 라이브러리

| 라이브러리 | 개발 PC 버전 | 용도 |
|-----------|-------------|------|
| `xlwings` | 0.33.12 | 엑셀 파일 열기, 사진 삽입, 저장 |

> xlwings를 설치하면 Windows에서 Excel을 제어하는 데 필요한 `pywin32`도 자동으로 함께 설치됩니다.

### 2-2. 설치할 필요 없는 라이브러리 (Python 기본 내장)

| 라이브러리 | 용도 |
|-----------|------|
| `os` | 파일/폴더 경로 처리, 탐색기 열기 |
| `shutil` | 사진 파일을 임시 폴더로 복사 |
| `tempfile` | 임시 폴더 위치 확인 |
| `tkinter` | 파일/폴더 선택 창, 완료 메시지 창 |

> `tkinter`는 python.org에서 받은 Windows용 Python에 기본으로 들어 있습니다.

---

## 3. 설치 명령어

새 컴퓨터에서 Python을 설치한 뒤 **터미널(PowerShell 또는 명령 프롬프트)**을 열고 아래 순서대로 입력하세요.

### ① Python 설치 확인
```powershell
python --version
```
`Python 3.x.x`처럼 버전이 나오면 정상입니다.

### ② pip 최신화 (선택)
```powershell
python -m pip install --upgrade pip
```

### ③ xlwings 설치 (필수)
```powershell
python -m pip install xlwings==0.33.12
```
개발 PC와 같은 버전으로 설치하는 명령입니다. 최신 버전을 쓰려면 `python -m pip install xlwings`를 입력하세요.

### ④ 설치 확인
```powershell
python -c "import xlwings; print(xlwings.__version__)"
```
`0.33.12`처럼 버전이 나오면 설치된 것입니다.

---

## 4. 실행 방법

터미널에서 이 파일이 있는 `CODE` 폴더로 이동한 뒤 실행합니다. 경로에 공백이 있으므로 **큰따옴표("")**로 감싸야 합니다.

```powershell
cd "코드가 있는 폴더 경로\CODE"
python "MOBIS 인자표 자동화_최종.py"
```

실행하면 아래 순서로 선택 창이 뜹니다.

1. 인자표 엑셀 파일(.xlsx) 선택
2. 전극사진 폴더 선택 → C20 셀부터 오른쪽으로 삽입
3. 금형사진 폴더 선택 → H58 셀부터 오른쪽으로 삽입
4. 제품사진 파일 선택 → C58 셀에 삽입

작업이 끝나면 원본 옆에 `파일명_updated.xlsx`가 저장되고(이미 있으면 `_updated_rev2`, `_rev3`…), 저장된 폴더가 자동으로 열립니다.

---

## 5. 자주 나는 문제

| 증상 | 원인 / 해결 |
|------|-------------|
| `'python'은(는) 내부 또는 외부 명령...이 아닙니다` | Python 설치 때 PATH 추가를 빠뜨렸습니다. Python을 다시 설치하면서 **"Add python.exe to PATH"**를 체크하거나, `python` 대신 `py`를 입력해 보세요. |
| `ModuleNotFoundError: No module named 'xlwings'` | xlwings가 설치되지 않았습니다. 3번의 ③ 명령을 실행하세요. Python이 여러 버전 설치된 PC라면, 설치할 때와 실행할 때 같은 Python을 써야 합니다. |
| 엑셀 관련 오류 창이 뜸 | Excel이 설치되어 있는지, 라이선스 인증이 되어 있는지 확인하세요. 작업 중 Excel이 멈췄다면 작업 관리자에서 `EXCEL.EXE`를 종료한 뒤 다시 실행하세요. |
| 사진이 안 들어감 | 지원하는 사진 형식은 `.png`, `.jpg`, `.jpeg`뿐입니다. |
