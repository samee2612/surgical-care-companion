@echo off
REM Quick Docker Desktop check and start script

echo Checking Docker Desktop status...

REM Check if Docker Desktop is running
docker version >nul 2>&1
if %errorlevel%==0 (
    echo [SUCCESS] Docker Desktop is running
    exit /b 0
)

echo [WARNING] Docker Desktop is not running
echo Attempting to start Docker Desktop...

REM Try to start Docker Desktop
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

if %errorlevel%==0 (
    echo [INFO] Docker Desktop is starting...
    echo [INFO] Please wait 30-60 seconds for Docker to fully start
    echo [INFO] You can check status with: docker version
    
    REM Wait and check again
    timeout /t 30 /nobreak >nul
    
    echo Checking Docker status again...
    docker version >nul 2>&1
    if %errorlevel%==0 (
        echo [SUCCESS] Docker Desktop is now running
        exit /b 0
    ) else (
        echo [WARNING] Docker Desktop may still be starting
        echo Please wait a moment and try again
        exit /b 1
    )
) else (
    echo [ERROR] Could not start Docker Desktop automatically
    echo Please start Docker Desktop manually:
    echo 1. Open Docker Desktop from Start Menu
    echo 2. Wait for it to fully start
    echo 3. Run the deployment script again
    pause
    exit /b 1
)
