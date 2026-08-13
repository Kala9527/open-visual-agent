@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\") do set "PROJECT_ROOT=%%~fI\"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%src;%PYTHONPATH%"

if not defined AGENT_CLI_SCRIPT (
    echo {"ok":false,"type":"error","operation":"agent_cli","error":{"kind":"ArgumentError","message":"AGENT_CLI_SCRIPT is not set.","status_code":null}}
    exit /b 2
)

if not exist "%SCRIPT_DIR%%AGENT_CLI_SCRIPT%" (
    echo {"ok":false,"type":"error","operation":"%AGENT_CLI_SCRIPT%","error":{"kind":"FileNotFoundError","message":"The requested Agent CLI script was not found.","status_code":null}}
    exit /b 1
)

set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

cd /d "%PROJECT_ROOT%" >nul 2>nul
if errorlevel 1 (
    echo {"ok":false,"type":"error","operation":"%AGENT_CLI_SCRIPT%","error":{"kind":"EnvironmentError","message":"Could not enter the project root.","status_code":null}}
    exit /b 1
)

"%PYTHON_EXE%" -c "import openai, dotenv, httpx, rich" >nul 2>nul
if errorlevel 1 (
    echo {"ok":false,"type":"error","operation":"%AGENT_CLI_SCRIPT%","error":{"kind":"DependencyError","message":"Missing Python packages. Run python -m pip install -r requirements.txt first.","status_code":null}}
    exit /b 1
)

"%PYTHON_EXE%" "%SCRIPT_DIR%%AGENT_CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%
