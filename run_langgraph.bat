@echo off
setlocal

set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

set LANGGRAPH=%~dp0.venv\Scripts\langgraph.exe

if not exist "%LANGGRAPH%" (
    echo Khong tim thay .venv\Scripts\langgraph.exe.
    echo Hay tao .venv Python 3.11+ va chay: .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

"%LANGGRAPH%" dev --no-browser
