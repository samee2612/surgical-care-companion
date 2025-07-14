#!/bin/bash

# TKA Voice Agent - Complete Docker Deployment Script
# This script builds and deploys all services with dependencies

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "🔍 Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_status "Docker is available"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_status "Docker Compose is available"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_status "Copying .env.example to .env"
        cp .env.example .env
        print_warning "Please update .env with your API keys before continuing"
        read -p "Press Enter after updating .env file..."
    fi
    print_status ".env file exists"
    
    # Check ngrok auth token
    if grep -q "your_ngrok_token_here" .env; then
        print_warning "ngrok auth token not configured in .env"
        print_status "You can get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    fi
}

# Build all Docker images
build_images() {
    print_header "🏗️ Building Docker Images"
    
    print_status "Building backend image..."
    docker-compose build backend
    
    print_status "Building ngrok image..."
    docker-compose build ngrok
    
    print_status "Building test runner image..."
    docker-compose build test-runner
    
    print_status "All images built successfully"
}

# Start services in order
start_services() {
    print_header "🚀 Starting Services"
    
    print_status "Starting infrastructure (PostgreSQL, Redis, pgAdmin)..."
    docker-compose up -d postgres redis pgadmin
    
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Wait for PostgreSQL to be ready
    echo -n "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker exec tka_postgres pg_isready -U user -d tka_voice >/dev/null 2>&1; then
            echo " Ready!"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    print_status "Starting backend service..."
    docker-compose up -d backend
    
    print_status "Waiting for backend to be ready..."
    sleep 15
    
    # Wait for backend to be healthy
    echo -n "Waiting for backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo " Ready!"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    print_status "Starting ngrok tunnel..."
    docker-compose up -d ngrok
    
    print_status "Starting test runner..."
    docker-compose up -d test-runner
    
    print_status "All services started successfully"
}

# Run database migrations
setup_database() {
    print_header "🗄️ Setting Up Database"
    
    print_status "Running database migrations..."
    docker exec tka_backend python -m alembic upgrade head
    
    print_status "Database setup complete"
}

# Get ngrok URL
get_ngrok_url() {
    print_header "🌐 Getting ngrok URL"
    
    sleep 5  # Wait for ngrok to start
    
    # Try to get ngrok URL
    for i in {1..10}; do
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
        
        if [ -n "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
            print_status "ngrok URL: $NGROK_URL"
            echo ""
            echo "🔧 Configure Twilio Webhook:"
            echo "  1. Go to: https://console.twilio.com"
            echo "  2. Navigate to: Phone Numbers → Manage → Active numbers"
            echo "  3. Click your phone number"
            echo "  4. Set Voice Webhook URL to: $NGROK_URL/api/v1/twilio/voice-webhook/"
            echo "  5. Set HTTP method to: POST"
            echo "  6. Save configuration"
            echo ""
            
            # Update .env file with ngrok URL
            if command -v sed &> /dev/null; then
                sed -i "s|TWILIO_WEBHOOK_URL=.*|TWILIO_WEBHOOK_URL=$NGROK_URL|" .env
                print_status "Updated .env file with ngrok URL"
            fi
            
            return 0
        fi
        
        echo -n "."
        sleep 2
    done
    
    print_warning "Could not get ngrok URL. Check if ngrok service is running."
    print_status "You can check manually at: http://localhost:4040"
}

# Show service status
show_status() {
    print_header "📊 Service Status"
    
    echo "🐳 Docker Services:"
    docker-compose ps
    echo ""
    
    echo "🔗 Service URLs:"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/health"
    echo "  • Database Admin: http://localhost:5050"
    echo "  • ngrok Web Interface: http://localhost:4040"
    echo ""
    
    echo "🔑 Database Admin Credentials:"
    echo "  • Email: admin@tka.com"
    echo "  • Password: admin"
    echo ""
    
    echo "📋 Quick Tests:"
    echo "  • Health Check: curl http://localhost:8000/health"
    echo "  • Twilio Status: curl http://localhost:8000/api/v1/calls/twilio-status"
    echo "  • Run Tests: ./scripts/test_components.sh"
    echo ""
}

# Main deployment function
main() {
    print_header "🎯 TKA Voice Agent - Docker Deployment"
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Run deployment steps
    check_prerequisites
    build_images
    start_services
    setup_database
    get_ngrok_url
    show_status
    
    print_header "✅ Deployment Complete!"
    
    echo ""
    echo "🎉 TKA Voice Agent is now running!"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Update Twilio webhook URL (see instructions above)"
    echo "  2. Test the system: ./scripts/test_components.sh"
    echo "  3. Make a test call: curl -X POST http://localhost:8000/api/v1/calls/initiate"
    echo "  4. Monitor logs: docker-compose logs -f backend"
    echo ""
    echo "🛑 To stop all services: docker-compose down"
    echo "🔄 To restart: docker-compose restart"
    echo "📊 To view logs: docker-compose logs -f [service_name]"
    echo ""
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy"|"")
        main
        ;;
    "stop")
        print_header "🛑 Stopping All Services"
        docker-compose down
        print_status "All services stopped"
        ;;
    "restart")
        print_header "🔄 Restarting All Services"
        docker-compose restart
        print_status "All services restarted"
        ;;
    "logs")
        print_header "📊 Showing Service Logs"
        docker-compose logs -f
        ;;
    "test")
        print_header "🧪 Running Component Tests"
        ./scripts/test_components.sh
        ;;
    "clean")
        print_header "🧹 Cleaning Up"
        docker-compose down -v
        docker system prune -f
        print_status "Cleanup complete"
        ;;
    *)
        echo "Usage: $0 [deploy|stop|restart|logs|test|clean]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy all services (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show service logs"
        echo "  test    - Run component tests"
        echo "  clean   - Clean up containers and volumes"
        exit 1
        ;;
esac
