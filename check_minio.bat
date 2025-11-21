@echo off
REM MinIO Status Check Script
REM Checks if MinIO server is running

echo ============================================================================
echo MinIO Server Status
echo ============================================================================
echo.

REM Check if MinIO is running
tasklist /FI "IMAGENAME eq minio.exe" 2>NUL | find /I /N "minio.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [STATUS] MinIO server is RUNNING
    echo.
    echo Server: http://localhost:9000
    echo Console: http://localhost:9001
    echo.
    echo Access Key: minioadmin
    echo Secret Key: minioadmin
    echo.
) else (
    echo [STATUS] MinIO server is NOT RUNNING
    echo.
    echo To start MinIO, run: start_minio.bat
    echo.
)

echo ============================================================================
pause
