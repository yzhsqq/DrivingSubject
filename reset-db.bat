@echo off
setlocal
cd /d "%~dp0"

rem ============================================================
rem   Reset database: drops all tables and re-imports them
rem   (schema.sql -^> init.sql -^> questions.sql -^> q_images.sql).
rem   Stop the backend first (run stop-system.bat) otherwise the
rem   import may fail or the running app may lose its tables.
rem   NOTE: this file must stay pure ASCII (no Chinese text) so that
rem   cmd.exe parses it correctly on any Windows code page.
rem ============================================================

rem Local configuration is intentionally excluded from Git.
set "DB_HOST=127.0.0.1"
set "DB_PORT=3306"
set "DB_USER=root"
set "DB_PASS="
set "DB_NAME=driving_subject1"
set "MYSQL="
if exist "%~dp0config.local.bat" call "%~dp0config.local.bat"
set "MYSQL_AUTH="
if defined DB_PASS set "MYSQL_AUTH=-p%DB_PASS%"

set "DB_DIR=%~dp0db"
if exist "%DB_DIR%\schema.sql" goto :db_ok
echo [ERROR] db\schema.sql not found. Run from project/release root.
pause
exit /b 1
:db_ok

call :find_mysql
if defined MYSQL goto :mysql_ok
echo [ERROR] mysql client not found. Set the MYSQL variable at the top of this script.
pause
exit /b 1
:mysql_ok

echo WARNING: this will DELETE all data in database %DB_NAME% and re-import it.
choice /c YN /m "Reset database now (Y), or abort (N)"
if errorlevel 2 exit /b 0

"%MYSQL%" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% %MYSQL_AUTH% -N -e "SELECT 1" >nul 2>nul
if not errorlevel 1 goto :conn_ok
echo [ERROR] Cannot connect to MySQL ^(%DB_HOST%:%DB_PORT%, user %DB_USER%^). Check the service and DB_PASS.
pause
exit /b 1
:conn_ok

call :run_sql schema.sql      "create tables"
if errorlevel 1 goto :fail
call :run_sql init.sql       "seed roles / permissions"
if errorlevel 1 goto :fail
call :run_sql questions.sql   "import 2309 questions"
if errorlevel 1 goto :fail
call :run_sql q_images.sql    "bind question images"
if errorlevel 1 goto :fail

echo.
echo Database %DB_NAME% has been reset successfully.
echo Start the system with start-system.bat
echo.
pause
exit /b 0

:fail
echo.
echo [ERROR] Reset failed - see messages above.
pause
exit /b 1

:find_mysql
if not "%MYSQL%"=="" goto :eof
where mysql >nul 2>nul
if not errorlevel 1 set "MYSQL=mysql"
if defined MYSQL goto :eof
if exist "E:\Web\MySQL\bin\mysql.exe" set "MYSQL=E:\Web\MySQL\bin\mysql.exe"
if defined MYSQL goto :eof
if exist "C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe" set "MYSQL=C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe"
if defined MYSQL goto :eof
if exist "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" set "MYSQL=C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"
if defined MYSQL goto :eof
if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" set "MYSQL=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if defined MYSQL goto :eof
if exist "C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe" set "MYSQL=C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe"
if defined MYSQL goto :eof
if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL=C:\xampp\mysql\bin\mysql.exe"
goto :eof

:run_sql
echo   applying %~1 (%~2) ...
"%MYSQL%" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% %MYSQL_AUTH% --default-character-set=utf8mb4 < "%DB_DIR%\%~1" >nul 2>nul
if errorlevel 1 goto :sql_fail
exit /b 0
:sql_fail
echo [ERROR] Failed to execute %~1.
exit /b 1
