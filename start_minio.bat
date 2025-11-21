@echo off
REM MinIO Server Startup Script
REM Starts a local MinIO S3-compatible object storage server

echo ============================================================================
echo Starting MinIO Server
echo ============================================================================
echo.

REM Create data directory if it doesn't exist
if not exist "minio_data" (
    echo Creating MinIO data directory...
    mkdir minio_data
)

REM Check if MinIO is already running
tasklist /FI "IMAGENAME eq minio.exe" 2>NUL | find /I /N "minio.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] MinIO is already running!
    echo          Please close existing MinIO instance first.
    echo.
    pause
    exit /b 1
)

echo Starting MinIO server on localhost:9000
echo Console: http://localhost:9001
echo.
echo Access Key: minioadmin
echo Secret Key: minioadmin
echo.
echo Press Ctrl+C to stop the server
echo ============================================================================
echo.

REM Start MinIO server
minio.exe server minio_data --console-address ":9001"

echo.
echo MinIO server stopped.
pause
