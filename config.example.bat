@echo off
rem Copy this file to config.local.bat, then fill in values for your machine.
rem config.local.bat is ignored by Git and must never be committed.

set "DB_HOST=127.0.0.1"
set "DB_PORT=3306"
set "DB_USER=root"
set "DB_PASS="
set "DB_NAME=driving_subject1"
set "APP_PORT=8080"
rem Set a long, unique value before any shared or public deployment.
set "JWT_SECRET="

rem Optional: set the full path when mysql.exe is not on PATH.
rem set "MYSQL=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
