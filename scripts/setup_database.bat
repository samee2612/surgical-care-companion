@echo off
REM TKA Voice Agent - Windows Database Setup Script
REM This script initializes the PostgreSQL database with all required tables and data

echo 🔧 Setting up TKA Voice Agent Database...

REM Configuration
set DB_NAME=tka_voice
set DB_USER=user
set DB_PASSWORD=password
set DB_HOST=localhost
set DB_PORT=5432

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo ❌ Please run this script from the project root directory
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not in PATH
    exit /b 1
)

echo 📊 Checking PostgreSQL connection...
REM Start PostgreSQL with Docker if not running
docker-compose up -d postgres redis
echo ✅ PostgreSQL and Redis started

REM Wait a moment for services to start
timeout /t 10 /nobreak >nul

echo 🐍 Setting up Python environment...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Check if alembic is configured
if not exist "alembic.ini" (
    echo ❌ Alembic configuration not found
    echo Please ensure alembic.ini exists in the backend directory
    exit /b 1
)

REM Run database migrations
echo 🗄️ Running database migrations...
python -m alembic upgrade head

if errorlevel 1 (
    echo ❌ Database migration failed
    exit /b 1
)

echo ✅ Database migrations completed successfully

REM Initialize test data (optional)
echo 🧪 Initializing test data...
if exist "scripts\init_db.py" (
    python scripts\init_db.py
    echo ✅ Test data initialized
) else (
    echo ⚠️ No test data script found, skipping...
)

REM Verify database setup
echo 🔍 Verifying database setup...
python -c "import os; import sys; sys.path.append('.'); from database.connection import get_database; from sqlalchemy import text; db = next(get_database()); result = db.execute(text('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = ''public''')); table_count = result.scalar(); print(f'✅ Database setup verified: {table_count} tables found'); db.close()"

if errorlevel 1 (
    echo ❌ Database verification failed
    exit /b 1
)

echo.
echo 🎉 Database setup completed successfully!
echo.
echo 📝 Next steps:
echo 1. Copy .env.example to .env and configure your environment variables
echo 2. Start the backend service: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo 3. Visit http://localhost:8000/docs to see the API documentation
echo.
echo 🔗 Useful links:
echo - API Documentation: http://localhost:8000/docs
echo - Database Admin: http://localhost:5050 (admin@tka.com / admin)
echo - Health Check: http://localhost:8000/health

cd ..
pause
