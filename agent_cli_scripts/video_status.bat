@echo off
setlocal EnableExtensions
set "AGENT_CLI_SCRIPT=video_status.py"
call "%~dp0_run_with_env.bat" %*
exit /b %ERRORLEVEL%
