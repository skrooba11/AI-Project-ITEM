# MOBIS 시운전완료보고자료 자동화 - 실행 환경 및 필요 라이브러리

대상 실행 파일: `MOBIS 시운전완료보고자료 자동화_최종.py`

## 1. Python 버전

- **Python 3.10 이상** 권장 (개발 환경: Python 3.10.10, Windows 11)
- 설치 시 **"tcl/tk and IDLE"** 옵션이 체크되어 있어야 합니다. (기본값으로 체크되어 있음 — GUI 창(tkinter)에 필요)
- 설치 시 **"Add python.exe to PATH"** 를 체크하면 터미널에서 `python`, `pip` 명령을 바로 사용할 수 있습니다.

다운로드: https://www.python.org/downloads/

## 2. 추가 설치가 필요한 라이브러리

| 라이브러리 | 개발 환경 버전 | 용도 |
|---|---|---|
| `openpyxl` | 3.1.5 | 엑셀(.xlsx) 파일 읽기/쓰기, 셀 서식 복사, 이미지 삽입 |
| `Pillow` | 11.2.1 | openpyxl이 엑셀에 이미지(png/jpg/bmp/gif)를 삽입할 때 내부적으로 사용 (**없으면 이미지 삽입 시 오류 발생**) |

## 3. 설치 명령어 (터미널 / 명령 프롬프트 / PowerShell에 입력)

```
pip install openpyxl==3.1.5 Pillow==11.2.1
```

`pip` 명령이 인식되지 않으면 아래 명령을 대신 사용하세요.

```
python -m pip install openpyxl==3.1.5 Pillow==11.2.1
```

(최신 버전을 설치해도 동작에 문제는 없을 것으로 예상되며, 문제가 생기면 위의 버전 고정 명령을 사용하세요.)

설치 확인:

```
python -c "import openpyxl, PIL, tkinter; print('openpyxl', openpyxl.__version__, '/ Pillow', PIL.__version__, '/ tkinter OK')"
```

## 4. 별도 설치가 필요 없는 라이브러리 (Python 기본 내장)

`os`, `re`, `shutil`, `copy`, `traceback`, `tkinter` (filedialog, messagebox)

## 5. 실행 방법

`CODE` 폴더에서 터미널을 열고 아래 명령을 입력합니다.

```
python "MOBIS 시운전완료보고자료 자동화_최종.py"
```

## 6. 참고 사항

- 입력/출력 엑셀 파일은 **.xlsx** 형식만 지원합니다. (.xls, .xlsm 파일은 엑셀에서 .xlsx로 다시 저장 후 사용)
- 원본 파일에 매크로(VBA)가 있어도 결과 파일에는 매크로가 포함되지 않습니다. (`keep_vba=False`)
- 지원 이미지 형식: .png, .jpg, .jpeg, .bmp, .gif
- GUI 글꼴로 "맑은 고딕"을 사용하므로 Windows 환경에서 실행하는 것을 권장합니다.
- 실행 시 대상 엑셀 파일이 Excel에서 열려 있으면 저장이 실패할 수 있으니, 실행 전 파일을 닫아 주세요.
