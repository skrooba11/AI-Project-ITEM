@echo off
cd /d "%~dp0"
echo MK 업무기록 웹 서버를 시작합니다 (http://192.168.134.130:8003)
echo 이 창을 닫으면 서버가 종료됩니다.
python app.py
pause
