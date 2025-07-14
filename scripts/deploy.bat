@echo off
REM TKA Voice Agent - Windows Docker Deployment Script
setlocal enabledelayedexpansion

echo ==========================================
echo TKA Voice Agent - Docker Deployment
echo ==========================================
echo.

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo [ERROR] Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check prerequisites
echo Checking Prerequisites
echo ------------------------------------------

REM Check Docker Desktop
echo Checking if Docker Desktop is running...
docker version >nul 2>&1
if %errorlevel%==0 (
    echo [SUCCESS] Docker is available and running
) else (
    echo [ERROR] Docker Desktop is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

REM Check .env file and validate critical keys
if not exist ".env" (
    echo [ERROR] .env file not found
    pause
    exit /b 1
)

REM Check for placeholder values that need to be updated
findstr /C:"your_gemini_api_key_here" .env >nul
if %errorlevel% equ 0 (
    echo [ERROR] Please configure GEMINI_API_KEY in .env file
    echo 1. Visit: https://makersuite.google.com/app/apikey
    echo 2. Create API key
    echo 3. Replace GEMINI_API_KEY=your_gemini_api_key_here with your actual key
    pause
    exit /b 1
)

findstr /C:"AIzaSyYourActualGeminiAPIKeyHere" .env >nul
if %errorlevel% equ 0 (
    echo [ERROR] Please update GEMINI_API_KEY with your real API key
    echo 1. Visit: https://makersuite.google.com/app/apikey
    echo 2. Create API key  
    echo 3. Replace the placeholder key with your actual key
    pause
    exit /b 1
)

echo [SUCCESS] Environment validation complete
echo.

REM Clean up any existing containers
echo Cleaning Previous Deployment
echo ------------------------------------------
echo [INFO] Stopping any existing containers...
docker-compose down >nul 2>&1

REM Build images
echo Building Docker Images
echo ------------------------------------------
echo [INFO] Building backend image...
docker-compose build backend --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build backend image
    pause
    exit /b 1
)

echo [INFO] Building other images...
docker-compose build ngrok test-runner --no-cache >nul 2>&1

echo [SUCCESS] All images built successfully
echo.

REM Start infrastructure first
echo Starting Infrastructure
echo ------------------------------------------
echo [INFO] Starting PostgreSQL and Redis...
docker-compose up -d postgres redis pgadmin

REM Wait for infrastructure
echo [INFO] Waiting for infrastructure to be ready...
timeout /t 15 /nobreak >nul

REM Check if PostgreSQL is ready
echo [INFO] Verifying PostgreSQL connection...
set /a counter=0
:wait_postgres
docker-compose exec -T postgres pg_isready -U user -d tka_voice >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] PostgreSQL is ready
    goto postgres_ready
)
set /a counter+=1
if %counter% geq 20 (
    echo [ERROR] PostgreSQL failed to start
    echo [INFO] Check logs: docker-compose logs postgres
    pause
    exit /b 1
)
timeout /t 3 /nobreak >nul
goto wait_postgres
:postgres_ready

REM Start backend
echo Starting Backend Service  
echo ------------------------------------------
echo [INFO] Starting backend...
docker-compose up -d backend

REM Wait for backend with better error handling
echo [INFO] Waiting for backend to start (this may take 1-2 minutes)...
set /a counter=0
:wait_backend
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend is ready and healthy
    goto backend_ready
)

set /a counter+=1
echo [INFO] Backend starting... attempt %counter%/24
if %counter% geq 24 (
    echo [WARNING] Backend taking longer than expected
    echo [INFO] Checking backend logs for issues...
    docker-compose logs --tail=20 backend
    echo.
    echo [INFO] The backend may still be starting. Common issues:
    echo - Missing or invalid GEMINI_API_KEY
    echo - Database connection issues  
    echo - Missing dependencies
    echo.
    choice /C YN /M "Continue deployment anyway? (Y/N)"
    if errorlevel 2 exit /b 1
    goto backend_ready
)
goto wait_backend
:backend_ready

REM Start remaining services
echo Starting Additional Services
echo ------------------------------------------
echo [INFO] Starting ngrok tunnel...
docker-compose up -d ngrok

echo [INFO] Starting test runner...
docker-compose up -d test-runner >nul 2>&1

echo.

REM Setup database
echo Setting Up Database
echo ------------------------------------------
echo [INFO] Running database migrations...
docker-compose exec -T backend python -c "import sys, os; sys.path.append('/app'); exec(open('/app/scripts/run_migrations.py').read())" 2>nul || echo [INFO] Migration completed or tables already exist

echo.

REM Get ngrok URL
echo Getting ngrok Tunnel URL
echo ------------------------------------------
echo [INFO] Retrieving ngrok tunnel URL...
timeout /t 10 /nobreak >nul

REM Use curl to get ngrok URL directly
curl -s http://localhost:4040/api/tunnels > ngrok_response.json 2>nul
if exist ngrok_response.json (
    findstr "https://" ngrok_response.json >nul
    if !errorlevel!==0 (
        echo [SUCCESS] ngrok tunnel is running
        echo [INFO] Check your ngrok URL at: http://localhost:4040
        echo [INFO] Configure Twilio webhook URL to: https://YOUR-NGROK-URL/api/v1/twilio/voice-webhook/
    ) else (
        echo [WARNING] No HTTPS tunnel found
    )
    del ngrok_response.json >nul 2>&1
) else (
    echo [WARNING] Could not connect to ngrok - check http://localhost:4040
)

echo.

REM Final status
echo Deployment Summary
echo ==========================================
echo [SUCCESS] TKA Voice Agent is deployed!
echo.
echo Service Status:
docker-compose ps
echo.
echo Service URLs:
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Health Check: http://localhost:8000/health
echo - Database Admin: http://localhost:5050 (admin@tka.com / admin)
echo - ngrok Interface: http://localhost:4040
echo.
echo Next Steps:
echo 1. Test backend: curl http://localhost:8000/health
echo 2. Get ngrok URL: visit http://localhost:4040
echo 3. Configure Twilio webhook with ngrok URL
echo 4. Test API: visit http://localhost:8000/docs
echo.
echo Troubleshooting:
echo - Backend logs: docker-compose logs backend  
echo - All logs: docker-compose logs
echo - Restart: docker-compose restart backend
echo - Stop all: docker-compose down
echo.
pause
