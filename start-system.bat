@echo off
setlocal
cd /d "%~dp0"

rem ============================================================
rem   Driving Subject1 (Driving-License Written-Exam System) - One-key launcher
rem
rem   Works both in the source tree and inside the release package.
rem   First run initializes the database automatically (schema.sql,
rem   init.sql, questions.sql, q_images.sql), then starts the backend
rem   on port 8080 and opens the browser.
rem
rem   If your MySQL differs, edit the options below.
rem   NOTE: this file must stay pure ASCII (no Chinese text) so that
rem   cmd.exe parses it correctly on any Windows code page.
rem ============================================================

rem Local configuration is intentionally excluded from Git.
set "DB_HOST=127.0.0.1"
set "DB_PORT=3306"
set "DB_USER=root"
set "DB_PASS="
set "DB_NAME=driving_subject1"
set "APP_PORT=8080"
set "JWT_SECRET="
set "MYSQL="
if exist "%~dp0config.local.bat" call "%~dp0config.local.bat"
if defined JWT_SECRET goto :jwt_secret_ready
for /f "delims=" %%s in ('powershell -NoProfile -Command "$b=New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)"') do set "JWT_SECRET=%%s"
echo [INFO] Generated a temporary JWT secret for this run. Set JWT_SECRET in config.local.bat to keep it stable.
:jwt_secret_ready
set "APP_URL=http://localhost:%APP_PORT%/"
set "MYSQL_AUTH="
if defined DB_PASS set "MYSQL_AUTH=-p%DB_PASS%"

rem ==================== locate jar / db ====================
set "JAR="
if exist "%~dp0app\driving-subject1.jar" set "JAR=%~dp0app\driving-subject1.jar"
if not defined JAR if exist "%~dp0backend\target\driving-subject1.jar" set "JAR=%~dp0backend\target\driving-subject1.jar"
if defined JAR goto :jar_ok
echo [ERROR] driving-subject1.jar not found.
echo         Expected: app\driving-subject1.jar (release)
echo         or       : backend\target\driving-subject1.jar (source)
echo         Please build the jar first (run one-click-package.bat).
pause
exit /b 1
:jar_ok

set "DB_DIR=%~dp0db"
if exist "%DB_DIR%\schema.sql" goto :db_ok
echo [ERROR] db\schema.sql not found. Script must be run from project/release root.
pause
exit /b 1
:db_ok

rem ==================== java ====================
where java >nul 2>nul
if not errorlevel 1 goto :java_ok
echo [ERROR] java not found in PATH. Please install JDK 8 or newer.
pause
exit /b 1
:java_ok

rem ==================== find mysql client ====================
call :find_mysql
if defined MYSQL goto :mysql_ok
echo [ERROR] mysql client not found.
echo         Please set the MYSQL variable at the top of this script,
echo         e.g.  set "MYSQL=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
pause
exit /b 1
:mysql_ok

rem ==================== port already in use? ====================
netstat -ano | findstr /r /c:":%APP_PORT% .*LISTENING" >nul 2>nul
if errorlevel 1 goto :port_free
echo [WARN] Port %APP_PORT% is already in use.
echo        The system may already be running. If not, stop that program first.
choice /c YN /m "Open browser and exit (Y), or abort (N)"
if errorlevel 2 exit /b 1
start "" "%APP_URL%"
exit /b 0
:port_free

rem ==================== mysql reachable? ====================
echo [1/3] Checking MySQL connection at %DB_HOST%:%DB_PORT% ...
"%MYSQL%" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% %MYSQL_AUTH% -N -e "SELECT 1" >nul 2>nul
if not errorlevel 1 goto :mysql_up
echo [ERROR] Cannot connect to MySQL ^(%DB_HOST%:%DB_PORT%, user %DB_USER%^).
echo         - Is the MySQL service running?
echo         - Does the password match? Set DB_PASS in config.local.bat.
pause
exit /b 1
:mysql_up

rem ==================== initialize on first run ====================
"%MYSQL%" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% %MYSQL_AUTH% -N -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='%DB_NAME%'" > "%TEMP%\_ds_dbchk.txt" 2>nul
set /p DBCNT=<"%TEMP%\_ds_dbchk.txt"
del "%TEMP%\_ds_dbchk.txt" >nul 2>nul
if not "%DBCNT%"=="0" goto :db_exists
echo [2/3] Database %DB_NAME% not found - initializing ^(one-time, may take a while^) ...
call :run_sql schema.sql      "create tables"
if errorlevel 1 goto :init_fail
call :run_sql init.sql       "seed roles / permissions"
if errorlevel 1 goto :init_fail
call :run_sql questions.sql   "import 2309 questions"
if errorlevel 1 goto :init_fail
call :run_sql q_images.sql    "bind question images"
if errorlevel 1 goto :init_fail
echo         Database initialized.
goto :db_ready
:db_exists
echo [2/3] Database %DB_NAME% already exists - skip initialization.
:db_ready

rem ==================== start backend ====================
echo [3/3] Starting backend on port %APP_PORT% ...
set "SPRING_DATASOURCE_PASSWORD=%DB_PASS%"
start "" /b java -jar "%JAR%" --server.port=%APP_PORT% --spring.datasource.url="jdbc:mysql://%DB_HOST%:%DB_PORT%/%DB_NAME%?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true" --spring.datasource.username=%DB_USER% --mybatis-plus.configuration.log-impl=org.apache.ibatis.logging.nologging.NoLoggingImpl > "%~dp0app.log" 2>&1

rem ==================== wait for readiness ====================
echo Waiting for the service to be ready ...
set /a TRIES=0
:waitloop
timeout /t 1 /nobreak >nul
set /a TRIES+=1
set "HTTP="
for /f "delims=" %%c in ('powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:%APP_PORT%/index.html' -TimeoutSec 2).StatusCode } catch {}"') do set "HTTP=%%c"
if "%HTTP%"=="200" goto :ready
if %TRIES% geq 60 goto :timeout
goto :waitloop

:ready
echo Ready. Opening browser ...
start "" "%APP_URL%"
echo.
echo ============================================================
echo   System is running at: %APP_URL%
echo   Log file: %~dp0app.log
echo.
echo   Demo accounts (password: 123456)
echo     admin           -^> System admin
echo     questionadmin   -^> Question admin
echo     student         -^> Student
echo   Stop: run stop-system.bat
echo ============================================================
echo.
pause
exit /b 0

:timeout
echo [WARN] Service did not answer on /index.html within 60s.
echo        The jar may be an old API-only build without the web UI.
echo        Rebuild with one-click-package.bat, then retry.
echo        Last log lines:
type "%~dp0app.log" 2>nul
pause
exit /b 1

:init_fail
echo.
echo [ERROR] Database initialization failed - see messages above.
echo         You can also import the SQL files manually with a MySQL client.
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
echo     applying %~1 (%~2) ...
"%MYSQL%" -h%DB_HOST% -P%DB_PORT% -u%DB_USER% %MYSQL_AUTH% --default-character-set=utf8mb4 < "%DB_DIR%\%~1" >nul 2>nul
if errorlevel 1 goto :sql_fail
exit /b 0
:sql_fail
echo [ERROR] Failed to execute %~1.
exit /b 1
