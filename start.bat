@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%src;%PYTHONPATH%"

cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8007 --reload
