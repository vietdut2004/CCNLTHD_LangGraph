@echo off
setlocal
set PYTHONIOENCODING=utf-8
set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PROJECT_PYTHON%" set "PROJECT_PYTHON=python"
pushd "%~dp0"
"%PROJECT_PYTHON%" "%~dp0start_api.py"
set "RUN_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %RUN_EXIT_CODE%
