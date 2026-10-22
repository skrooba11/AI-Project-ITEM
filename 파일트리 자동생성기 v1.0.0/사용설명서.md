# 파일트리 자동생성기 v2.0 - 실행 환경 및 필요 라이브러리

대상 코드: `파일트리 자동생성기 v2.0_최종코드.py`

## 1. Python 버전

- **Python 3.10 이상 권장** (개발 환경: Python 3.10.10)
- 설치: https://www.python.org/downloads/
  - Windows 설치 시 **"Add Python to PATH"** 와 **"tcl/tk and IDLE"** 옵션을 반드시 체크하세요. (tkinter 포함)

설치 확인:

```bash
python --version
```

## 2. 별도 설치가 필요한 외부 라이브러리

| 라이브러리 | 개발 환경 버전 | 용도 |
|---|---|---|
| `customtkinter` | 5.2.2 | 모던 스타일 GUI 위젯 |
| `tkinterdnd2` | 0.4.3 | 파일/폴더 드래그 앤 드롭 기능 |

### 설치 명령어 (터미널 / 명령 프롬프트 / PowerShell에 입력)

```bash
pip install customtkinter==5.2.2 tkinterdnd2==0.4.3
```

`pip` 명령이 인식되지 않을 경우:

```bash
python -m pip install customtkinter==5.2.2 tkinterdnd2==0.4.3
```

> 버전을 고정하지 않고 최신 버전으로 설치하려면 `pip install customtkinter tkinterdnd2` 를 사용해도 됩니다.

설치 확인:

```bash
python -m pip show customtkinter tkinterdnd2
```

## 3. 설치가 필요 없는 표준 라이브러리 (Python 기본 포함)

`tkinter` (`ttk`, `simpledialog`, `filedialog`, `messagebox` 포함), `os`, `sys`, `pickle`, `subprocess`, `shutil`, `copy`, `traceback`

> **Linux 사용자 참고:** 일부 배포판은 tkinter가 기본 포함되지 않습니다. 필요 시 설치하세요.
>
> ```bash
> sudo apt install python3-tk      # Ubuntu / Debian
> ```

## 4. 실행 방법

코드 파일이 있는 `CODE` 폴더에서 아래 명령어를 실행합니다. (파일명에 공백이 있으므로 따옴표 필수)

```bash
python "파일트리 자동생성기 v2.0_최종코드.py"
```

## 5. 한 번에 설치 + 실행 (요약)

```bash
python -m pip install customtkinter==5.2.2 tkinterdnd2==0.4.3
python "파일트리 자동생성기 v2.0_최종코드.py"
```

## 6. 참고 사항

- 템플릿 데이터는 `filetree_templates.pkl` 파일에 저장됩니다. 이 파일은 **프로그램을 실행한 현재 폴더(터미널 위치)** 기준으로 읽고 저장됩니다. 기존 템플릿을 그대로 사용하려면 이 파일을 실행 위치에 함께 복사하세요.
- 폴더 열기 기능은 Windows(`os.startfile`), macOS(`open`), Linux(`xdg-open`)를 모두 지원합니다.
