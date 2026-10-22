# 폼텍 라벨 디자인 편집기 – 실행 요구사항 (Requirements)

이 프로그램은 **Electron** 기반 데스크톱 앱입니다.
화면은 `폼텍 라벨 디자인 편집기.html` 한 파일로 되어 있고, `main.js`가 Electron 창을 띄워 그 HTML을 불러옵니다.

---

## 1. 시스템 요구사항

| 항목 | 요구사항 | 비고 |
|------|----------|------|
| OS | Windows 10 / 11 (64bit) | 빌드 설정이 Windows portable 기준 |
| Node.js | **v22.x LTS** 권장 (개발 환경: v22.19.0) | https://nodejs.org 에서 LTS 설치 |
| npm | v10.x 이상 (개발 환경: 10.9.3) | Node.js 설치 시 함께 설치됨 |
| 인터넷 | 최초 `npm install` 할 때 필요 | Electron 바이너리(약 100MB)를 내려받음 |

설치 확인:
```bash
node -v
npm -v
```

---

## 2. 필요한 라이브러리 (npm 패키지)

`package.json`에 이미 정의되어 있어 `npm install` 한 번이면 모두 설치됩니다.

### 실행에 필요한 패키지 (dependencies)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `xlsx` (SheetJS) | ^0.18.5 | 금형번호 엑셀(.xlsx / .xls / .xlsm) 파일 읽기 |

### 개발·빌드에 필요한 패키지 (devDependencies)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `electron` | ^39.2.7 | 데스크톱 앱 실행 환경 (`npm start`) |
| `electron-builder` | ^26.0.12 | Windows 실행 파일(.exe) 빌드 (`npm run build`) |

### Node.js 기본 모듈 (따로 설치하지 않음)
- `fs`: 백업 JSON과 엑셀 파일 읽기, PDF 저장
- `path`: 파일 경로 처리

### CDN 스크립트 (따로 설치하지 않음)
- HTML 안에서 `https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js`를 함께 불러옵니다.
  로컬 `node_modules/xlsx`를 먼저 쓰므로 **오프라인이어도 엑셀 기능은 동작합니다.**

---

## 3. 다른 컴퓨터에서 설치하고 실행하기

### 3-1. 복사할 파일
아래 파일을 새 컴퓨터의 같은 폴더에 복사합니다. (`node_modules`, `dist`, `백업`, `tmpclaude-*` 폴더와 파일은 **복사하지 않아도 됩니다**.)

```
main.js                          ← 필수 (Electron 진입점)
폼텍 라벨 디자인 편집기.html       ← 필수 (프로그램 본체)
package.json                     ← 필수 (라이브러리 목록)
package-lock.json                ← 권장 (똑같은 버전으로 설치)
icon.ico / icon.png              ← 빌드 시 필요
label-designer-backup.json       ← 선택 (저장된 템플릿과 레이아웃이 시작할 때 자동으로 불러와짐)
@금형번호.xlsm                    ← 선택 (네트워크 경로를 쓸 수 없을 때 대신 쓰는 로컬 금형번호 데이터)
```

### 3-2. 라이브러리 설치
프로젝트 폴더에서 터미널(PowerShell 또는 명령 프롬프트)을 열고 실행합니다.

```bash
npm install
```
> `package-lock.json`이 있으면 `npm ci`를 쓰면 개발 PC와 완전히 같은 버전으로 설치됩니다.

### 3-3. 실행
```bash
npm start
```

### 3-4. (선택) 실행 파일(.exe) 빌드
```bash
npm run build
```
→ `dist/` 폴더에 `폼텍 라벨 디자인 편집기 1.0.0.exe` (portable)가 만들어집니다.
빌드된 exe는 Node.js가 없는 PC에서도 바로 실행됩니다.

---

## 4. 외부 데이터 파일 경로 (참고)

프로그램은 시작할 때 금형번호 엑셀 파일을 아래 순서로 찾습니다.

1. 네트워크 경로: `\\mk-net\문서\2. 영업\금형번호\금형번호.xlsm`
2. 로컬 경로: 프로그램 폴더의 `@금형번호.xlsm`

사내 네트워크에 연결되지 않은 PC라면 `@금형번호.xlsm`을 프로그램 폴더에 함께 두세요.
둘 다 없어도 프로그램은 실행되며, 화면에서 엑셀 파일을 직접 선택해 불러올 수 있습니다.

---

## 5. 문제 해결

| 증상 | 해결 방법 |
|------|-----------|
| `'electron'은(는) 내부 또는 외부 명령...이 아닙니다` | `npm install`을 하지 않은 상태입니다. 먼저 설치하세요. |
| Electron 다운로드가 실패하거나 멈춤 | 사내 방화벽이나 프록시 문제일 수 있습니다. `npm config set proxy http://프록시주소:포트` 설정 후 다시 시도하세요. |
| 금형번호 검색이 비어 있음 | 4번의 엑셀 파일 경로를 확인하세요. 개발자 도구(F12) 콘솔에서 로드 로그를 볼 수 있습니다. |
| `npm` 명령을 찾을 수 없음 | Node.js를 설치한 뒤 터미널을 다시 여세요. |
