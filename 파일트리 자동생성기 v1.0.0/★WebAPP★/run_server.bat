@echo off
setlocal
cd /d "%~dp0"
set PYTHON_EXE=C:\Users\Mktech\AppData\Local\Programs\Python\Python310\python.exe

:loop
echo [%date% %time%] server starting >> server.log
"%PYTHON_EXE%" app.py >> server.log 2>&1
echo [%date% %time%] server stopped - restarting in 5s >> server.log
timeout /t 5 /nobreak >nul
goto loop
