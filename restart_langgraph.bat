@echo off
call "%~dp0run_langgraph.bat" --restart %*
exit /b %errorlevel%
