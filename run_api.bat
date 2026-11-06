@echo off
setlocal
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
"%PYTHON%" "%~dp0start_langgraph.py" %*
set "CHATBOT_EXIT_CODE=%errorlevel%"
if not "%CHATBOT_EXIT_CODE%"=="0" (
    echo.
    echo Khong khoi dong duoc chatbot. Xem thong bao loi ben tren.
    pause
)
exit /b %CHATBOT_EXIT_CODE%
