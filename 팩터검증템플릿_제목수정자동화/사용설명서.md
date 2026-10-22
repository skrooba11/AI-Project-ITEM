# 실행 환경 및 필요 라이브러리 (requirement)

대상 파일: `팩터검증템플릿_제목수정자동화__최종 코드.py`

## 1. 실행 환경

| 항목 | 내용 |
|---|---|
| 운영체제 | **Windows** (코드에서 `os.startfile()`을 사용하므로 Windows 전용) |
| Python | **3.8 이상** (개발 환경: Python 3.10.10) |

## 2. 별도 설치가 필요한 라이브러리

| 라이브러리 | 코드에서 사용하는 부분 | 확인된 버전 |
|---|---|---|
| `python-pptx` | `from pptx import Presentation` 등 (PPTX 파일 읽기/수정/저장) | 1.0.2 |

> 참고: 코드에서는 `import pptx`로 불러오지만, 설치할 때 패키지 이름은 **`python-pptx`** 입니다. (`pip install pptx`가 아님에 주의)
>
> `python-pptx`를 설치하면 `lxml`, `Pillow`, `XlsxWriter`, `typing_extensions`가 의존성으로 자동 설치됩니다.

## 3. 설치 불필요 (Python 기본 내장 라이브러리)

| 라이브러리 | 용도 |
|---|---|
| `tkinter` | 파일 선택 창, MP번호/품명 입력 창 (GUI) |
| `re` | 정규식으로 슬라이드 제목 패턴 검색 |
| `os` | 저장 폴더 열기 |

> `tkinter`는 Windows용 공식 Python 설치 프로그램(python.org)에 기본 포함되어 있습니다.
> 설치 시 "tcl/tk and IDLE" 옵션을 해제했다면 Python 설치 프로그램을 다시 실행해 해당 옵션을 체크(Modify)해야 합니다.

## 4. 설치 명령어 (터미널 / 명령 프롬프트 / PowerShell)

```bash
pip install python-pptx==1.0.2
```

`pip` 명령이 인식되지 않으면 아래 명령을 사용하세요.

```bash
python -m pip install python-pptx==1.0.2
```

설치 확인:

```bash
python -c "import pptx, tkinter; print('pptx', pptx.__version__, '/ tkinter OK')"
```

## 5. 실행 방법

코드 파일이 있는 폴더에서 아래 명령을 실행합니다.

```bash
python "팩터검증템플릿_제목수정자동화__최종 코드.py"
```

실행 순서:
1. 수정할 PPTX 파일 선택
2. MP번호(앞 2자리, 뒤 1~3자리)와 품명 입력 후 "확인" 또는 Enter
3. 저장 위치 선택 → 저장 후 해당 폴더가 자동으로 열림

## 6. (선택) exe 파일로 다시 빌드하려면

Python이 설치되지 않은 PC에서 쓰려면 exe로 만들 수 있습니다. 이 경우에만 추가 설치가 필요합니다.

```bash
pip install pyinstaller
pyinstaller --onefile "팩터검증템플릿_제목수정자동화__최종 코드.py"
```

생성된 exe는 `dist` 폴더에 만들어집니다.
(코드의 오류/완료 메시지가 콘솔 창에 출력되므로 `--noconsole` 옵션은 넣지 않는 것을 권장합니다.)
