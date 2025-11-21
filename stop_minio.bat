@echo off
REM MinIO Server Stop Script
REM Stops the running MinIO server

echo ============================================================================
echo Stopping MinIO Server
echo ============================================================================
echo.

REM Check if MinIO is running
tasklist /FI "IMAGENAME eq minio.exe" 2>NUL | find /I /N "minio.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo [INFO] MinIO is not running.
    pause
    exit /b 0
)

REM Kill MinIO process
echo Stopping MinIO server...
taskkill /F /IM minio.exe >NUL 2>&1

if "%ERRORLEVEL%"=="0" (
    echo [SUCCESS] MinIO server stopped successfully.
) else (
    echo [ERROR] Failed to stop MinIO server.
)

echo.
pause
