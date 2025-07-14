#!/bin/bash

# TKA Voice Agent - Development Server Startup Script
# This script starts all services in the correct order for development

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STARTUP]${NC} $1"
}

print_header "🚀 Starting TKA Voice Agent Development Environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your API keys and configuration"
    exit 1
fi

# Start infrastructure services
print_status "📦 Starting infrastructure services (PostgreSQL, Redis, pgAdmin)..."
docker-compose up -d postgres redis pgadmin

# Wait for services to be ready
print_status "⏳ Waiting for services to be ready..."
sleep 10

# Check if database needs setup
print_status "🔍 Checking database status..."
cd backend

# Install dependencies if needed
if [ ! -d "venv" ]; then
    print_status "🐍 Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run migrations if needed
print_status "🗄️ Ensuring database is up to date..."
python -m alembic upgrade head

# Start the backend service
print_status "🔧 Starting FastAPI backend service..."
echo ""
echo "📋 Service URLs:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Database Admin: http://localhost:5050"
echo "  • Backend Logs: Check this terminal"
echo ""
echo "🔑 Database Admin Credentials:"
echo "  • Email: admin@tka.com"
echo "  • Password: admin"
echo ""
echo "⚠️ Don't forget to:"
echo "  • Configure ngrok for Twilio webhooks (see SETUP_GUIDE.md)"
echo "  • Update Twilio webhook URLs in console"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Start the FastAPI server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
