@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Create the virtual environment first. See README.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m maxbot
set "BOT_EXIT=%errorlevel%"
pause
exit /b %BOT_EXIT%
