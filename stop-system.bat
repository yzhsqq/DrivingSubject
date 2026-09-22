@echo off
setlocal
cd /d "%~dp0"

rem Stop the Driving Subject1 backend (java process listening on APP_PORT).
rem NOTE: this file must stay pure ASCII (no Chinese text) so that
rem cmd.exe parses it correctly on any Windows code page.

set "APP_PORT=8080"
set "FOUND="

for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%APP_PORT% .*LISTENING"') do call :try_kill %%p

if defined FOUND goto :was_found
echo No running java process found on port %APP_PORT% - nothing to stop.
goto :finish
:was_found
echo Backend process on port %APP_PORT% has been stopped.
:finish
echo Done.
pause
exit /b 0

:try_kill
tasklist /fi "PID eq %1" 2>nul | findstr /i "java.exe" >nul
if errorlevel 1 goto :eof
taskkill /f /pid %1 >nul 2>nul
if errorlevel 1 goto :eof
echo   Stopped process PID %1
set "FOUND=1"
goto :eof
