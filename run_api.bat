@echo off
setlocal

set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

set PYTHON=%~dp0.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    set PYTHON=python
)

"%PYTHON%" -m uvicorn main:app --reload
