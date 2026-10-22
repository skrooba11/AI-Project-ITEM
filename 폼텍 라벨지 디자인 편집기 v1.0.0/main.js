const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // 전체화면으로 시작
  mainWindow.maximize();

  // 한글 메뉴 설정
  const menuTemplate = [
    {
      label: '파일',
      submenu: [
        {
          label: '새로 만들기',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-command', 'new');
          }
        },
        {
          label: '불러오기',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-command', 'open');
          }
        },
        {
          label: '저장하기',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.send('menu-command', 'save');
          }
        },
        { type: 'separator' },
        {
          label: '인쇄',
          accelerator: 'CmdOrCtrl+P',
          click: () => {
            mainWindow.webContents.print({
              silent: false,
              printBackground: true,
              deviceName: ''
            });
          }
        },
        {
          label: 'PDF로 저장',
          click: async () => {
            const { dialog } = require('electron');
            const fs = require('fs');

            const result = await dialog.showSaveDialog(mainWindow, {
              title: 'PDF로 저장',
              defaultPath: 'label-design.pdf',
              filters: [
                { name: 'PDF 파일', extensions: ['pdf'] }
              ]
            });

            if (!result.canceled && result.filePath) {
              const pdfData = await mainWindow.webContents.printToPDF({
                printBackground: true,
                pageSize: 'A4'
              });

              fs.writeFile(result.filePath, pdfData, (err) => {
                if (err) {
                  dialog.showErrorBox('저장 실패', 'PDF 저장 중 오류가 발생했습니다.');
                } else {
                  dialog.showMessageBox(mainWindow, {
                    type: 'info',
                    title: '저장 완료',
                    message: 'PDF 파일이 저장되었습니다.'
                  });
                }
              });
            }
          }
        },
        { type: 'separator' },
        {
          label: '종료',
          accelerator: 'Alt+F4',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '편집',
      submenu: [
        {
          label: '실행 취소',
          accelerator: 'CmdOrCtrl+Z',
          click: () => {
            mainWindow.webContents.send('menu-command', 'undo');
          }
        },
        {
          label: '다시 실행',
          accelerator: 'CmdOrCtrl+Y',
          click: () => {
            mainWindow.webContents.send('menu-command', 'redo');
          }
        },
        { type: 'separator' },
        { label: '잘라내기', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: '복사', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: '붙여넣기', accelerator: 'CmdOrCtrl+V', role: 'paste' },
        {
          label: '삭제',
          accelerator: 'Delete',
          click: () => {
            mainWindow.webContents.send('menu-command', 'delete');
          }
        },
        { type: 'separator' },
        { label: '모두 선택', accelerator: 'CmdOrCtrl+A', role: 'selectAll' }
      ]
    },
    {
      label: '보기',
      submenu: [
        {
          label: '확대',
          accelerator: 'CmdOrCtrl+Plus',
          click: () => {
            mainWindow.webContents.send('menu-command', 'zoom-in');
          }
        },
        {
          label: '축소',
          accelerator: 'CmdOrCtrl+-',
          click: () => {
            mainWindow.webContents.send('menu-command', 'zoom-out');
          }
        },
        {
          label: '실제 크기',
          accelerator: 'CmdOrCtrl+0',
          click: () => {
            mainWindow.webContents.send('menu-command', 'zoom-reset');
          }
        },
        { type: 'separator' },
        { label: '새로 고침', accelerator: 'F5', role: 'reload' },
        { label: '전체 화면', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: '창',
      submenu: [
        { label: '최소화', role: 'minimize' },
        { label: '닫기', role: 'close' }
      ]
    },
    {
      label: '도움말',
      submenu: [
        {
          label: '개발자 도구',
          accelerator: 'F12',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        },
        { type: 'separator' },
        {
          label: '정보',
          click: () => {
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: '폼텍 라벨 디자인 편집기',
              message: '폼텍 라벨 디자인 편집기',
              detail: '버전 1.0.0\n\nA4 전용 라벨 디자인 도구'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  mainWindow.loadFile('폼텍 라벨 디자인 편집기.html');

  // 개발자 도구 열기 (디버깅용)
  // mainWindow.webContents.openDevTools();
}

// 창 포커스 리셋 IPC 핸들러 (입력 필드 먹통 해결의 핵심!)
ipcMain.on('reset-window-focus', () => {
  console.log('🔄 창 포커스 리셋 요청 받음');
  if (mainWindow) {
    // 창 blur 후 focus - 최소화/복원과 동일한 효과
    mainWindow.blur();
    setTimeout(() => {
      mainWindow.focus();
      // webContents에도 포커스
      mainWindow.webContents.focus();
      console.log('✅ 창 포커스 리셋 완료');
    }, 50);
  }
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
