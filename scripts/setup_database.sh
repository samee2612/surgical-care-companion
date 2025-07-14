#!/bin/bash

# TKA Voice Agent - Complete Database Setup Script
# This script initializes the PostgreSQL database with all required tables and data

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

print_header "🔧 Setting up TKA Voice Agent Database..."

# Configuration
DB_NAME="tka_voice"
DB_USER="user"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if PostgreSQL is running
print_status "📊 Checking PostgreSQL connection..."
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER >/dev/null 2>&1; then
    print_warning "PostgreSQL is not running on localhost:5432"
    print_status "Starting PostgreSQL with Docker..."
    docker-compose up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER >/dev/null 2>&1; then
            print_status "✅ PostgreSQL is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start after 30 seconds"
            exit 1
        fi
        sleep 1
    done
fi

# Change to backend directory
cd backend

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create initial migration
print_status "Creating initial database migration..."
if [ ! -f "alembic/versions/0001_initial_migration.py" ]; then
    alembic revision --autogenerate -m "Initial migration"
    print_status "Created initial migration"
else
    print_warning "Initial migration already exists"
fi

# Run migrations
print_status "Running database migrations..."
alembic upgrade head

# Initialize database with sample data
print_status "Initializing database with sample data..."
python scripts/init_db.py

# Verify database setup
print_status "Verifying database setup..."
python -c "
from database.connection import SessionLocal, check_db_connection
from models import Patient, ClinicalStaff, CallSession
import asyncio

async def verify():
    if not await check_db_connection():
        print('Database connection failed')
        exit(1)
    
    db = SessionLocal()
    try:
        staff_count = db.query(ClinicalStaff).count()
        patient_count = db.query(Patient).count()
        call_count = db.query(CallSession).count()
        
        print(f'Database verification successful:')
        print(f'  - Clinical Staff: {staff_count}')
        print(f'  - Patients: {patient_count}')
        print(f'  - Call Sessions: {call_count}')
    finally:
        db.close()

asyncio.run(verify())
"

cd ..

print_status "Database setup completed successfully!"
print_status "You can now start the application with:"
print_status "  docker-compose up -d"
print_status "  or"
print_status "  cd backend && python main.py" 