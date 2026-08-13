@echo off
setlocal EnableExtensions
set "AGENT_CLI_SCRIPT=generate_text.py"
call "%~dp0_run_with_env.bat" %*
exit /b %ERRORLEVEL%
