@echo off
setlocal

REM Call the PowerShell script. Pass first arg (optional folder) through.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_add_black_bars.ps1" -ImagesFolder "%~1"

endlocal
pause
