@echo off
REM TKA Voice Agent - Windows Development Server Startup Script
REM This script starts all services in the correct order for development

echo 🚀 Starting TKA Voice Agent Development Environment...

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️ WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your settings:
    echo   copy .env.example .env
    echo   # Edit .env with your API keys and configuration
    pause
    exit /b 1
)

REM Start infrastructure services
echo 📦 Starting infrastructure services ^(PostgreSQL, Redis, pgAdmin^)...
docker-compose up -d postgres redis pgadmin

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if database needs setup
echo 🔍 Checking database status...
cd backend

REM Install dependencies if needed
if not exist "venv" (
    echo 🐍 Setting up Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run migrations if needed
echo 🗄️ Ensuring database is up to date...
python -m alembic upgrade head

REM Start the backend service
echo 🔧 Starting FastAPI backend service...
echo.
echo 📋 Service URLs:
echo   • API Documentation: http://localhost:8000/docs
echo   • Health Check: http://localhost:8000/health
echo   • Database Admin: http://localhost:5050
echo   • Backend Logs: Check this terminal
echo.
echo 🔑 Database Admin Credentials:
echo   • Email: admin@tka.com
echo   • Password: admin
echo.
echo ⚠️ Don't forget to:
echo   • Configure ngrok for Twilio webhooks ^(see SETUP_GUIDE.md^)
echo   • Update Twilio webhook URLs in console
echo.
echo 🛑 Press Ctrl+C to stop all services
echo.

REM Start the FastAPI server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
