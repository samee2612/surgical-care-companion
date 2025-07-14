#!/bin/bash
# Surgical Care Companion - Comprehensive Testing Script
# =====================================================
# This script provides easy access to all testing workflows
# for the Surgical Care Companion system.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_services() {
    log_info "Checking service availability..."
    
    # Check if Docker Compose services are running
    if ! docker-compose ps | grep -q "Up"; then
        log_error "Docker Compose services are not running!"
        log_info "Starting services..."
        docker-compose up -d
        sleep 10
    fi
    
    # Check backend health
    if curl -s "$BASE_URL/health" > /dev/null; then
        log_success "Backend service is healthy"
    else
        log_error "Backend service is not responding"
        exit 1
    fi
    
    # Check database connectivity
    if docker-compose exec -T postgres pg_isready -U user > /dev/null 2>&1; then
        log_success "Database is ready"
    else
        log_error "Database is not ready"
        exit 1
    fi
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose exec -T backend python scripts/run_migrations.py
    
    # Initialize test data if needed
    if [ "$1" = "--with-test-data" ]; then
        log_info "Initializing test data..."
        docker-compose exec -T backend python scripts/setup_education_test.py
    fi
    
    log_success "Test environment ready"
}

run_unit_tests() {
    log_info "Running unit tests..."
    docker-compose exec -T backend python -m pytest tests/test_unit.py -v --tb=short
    log_success "Unit tests completed"
}

run_integration_tests() {
    log_info "Running integration tests..."
    docker-compose exec -T backend python -m pytest tests/test_integration.py -v --tb=short
    log_success "Integration tests completed"
}

run_comprehensive_tests() {
    log_info "Running comprehensive test suite..."
    python test_comprehensive.py --run-all --base-url "$BASE_URL"
    log_success "Comprehensive tests completed"
}

test_patient_workflow() {
    log_info "Testing complete patient workflow..."
    
    # Create test patient and verify call scheduling
    cat << 'EOF' > /tmp/test_patient.json
{
    "name": "Test Patient Workflow",
    "primary_phone_number": "+12132757114",
    "surgery_date": "2025-08-15T09:00:00Z",
    "primary_physician_id": "test-physician-id"
}
EOF
    
    log_info "Creating test patient..."
    PATIENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/patients/" \
        -H "Content-Type: application/json" \
        -d @/tmp/test_patient.json)
    
    if echo "$PATIENT_RESPONSE" | grep -q "id"; then
        log_success "Test patient created successfully"
        PATIENT_ID=$(echo "$PATIENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
        
        # Test call initiation
        log_info "Testing call initiation..."
        CALL_RESPONSE=$(curl -s -X POST "$BASE_URL/api/calls/initiate" \
            -H "Content-Type: application/json" \
            -d "{\"patient_id\": \"$PATIENT_ID\", \"call_type\": \"education\"}")
        
        if echo "$CALL_RESPONSE" | grep -q "call_session_id"; then
            log_success "Call initiated successfully"
        else
            log_error "Call initiation failed"
            echo "$CALL_RESPONSE"
        fi
    else
        log_error "Patient creation failed"
        echo "$PATIENT_RESPONSE"
    fi
    
    rm -f /tmp/test_patient.json
}

test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Test health endpoints
    curl -s "$BASE_URL/health" | grep -q "ok" && log_success "Main health endpoint OK" || log_error "Main health endpoint failed"
    curl -s "$BASE_URL/api/health" | grep -q "ok" && log_success "API health endpoint OK" || log_error "API health endpoint failed"
    
    # Test API endpoints with proper responses
    PATIENTS_RESPONSE=$(curl -s "$BASE_URL/api/patients/")
    if echo "$PATIENTS_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        log_success "Patients endpoint returning valid JSON"
    else
        log_error "Patients endpoint returning invalid response"
    fi
    
    STAFF_RESPONSE=$(curl -s "$BASE_URL/api/clinical/staff")
    if echo "$STAFF_RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        log_success "Clinical staff endpoint returning valid JSON"
    else
        log_error "Clinical staff endpoint returning invalid response"
    fi
}

test_speech_service() {
    log_info "Testing speech-to-text service..."
    
    # Check if speech service is running
    if curl -s "http://localhost:8001/health" > /dev/null; then
        log_success "Speech-to-text service is running"
        
        # Test with sample audio if available
        if [ -f "test/sample.wav" ]; then
            log_info "Testing audio transcription..."
            TRANSCRIBE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/voice-chat/transcribe" \
                -F "audio_file=@test/sample.wav")
            
            if echo "$TRANSCRIBE_RESPONSE" | grep -q "transcript"; then
                log_success "Audio transcription working"
            else
                log_warning "Audio transcription may have issues"
            fi
        else
            log_warning "No sample audio file found for testing"
        fi
    else
        log_warning "Speech-to-text service is not running"
    fi
}

test_twilio_integration() {
    log_info "Testing Twilio integration..."
    
    # Test webhook endpoint
    WEBHOOK_RESPONSE=$(curl -s -X POST "$BASE_URL/webhooks/twilio/voice" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "CallSid=test123&From=%2B12132757114&To=%2B18776589089&CallStatus=in-progress")
    
    if [ $? -eq 0 ]; then
        log_success "Twilio webhook endpoint responding"
    else
        log_error "Twilio webhook endpoint failed"
    fi
}

generate_test_report() {
    log_info "Generating test report..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    REPORT_FILE="test_report_$TIMESTAMP.txt"
    
    {
        echo "Surgical Care Companion - Test Report"
        echo "====================================="
        echo "Generated: $(date)"
        echo "Base URL: $BASE_URL"
        echo ""
        echo "Service Status:"
        docker-compose ps
        echo ""
        echo "System Information:"
        docker-compose exec -T backend python -c "
import psutil, platform
print(f'Python: {platform.python_version()}')
print(f'Platform: {platform.system()} {platform.release()}')
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
"
        echo ""
        echo "Database Tables:"
        docker-compose exec -T postgres psql -U user -d tka_voice -c "\dt"
        echo ""
        echo "Recent Logs:"
        docker-compose logs --tail=50 backend
    } > "$REPORT_FILE"
    
    log_success "Test report saved to $REPORT_FILE"
}

show_help() {
    cat << EOF
Surgical Care Companion - Testing Script
========================================

Usage: $0 [OPTION]

Options:
    setup                   Setup test environment
    setup --with-test-data  Setup with sample test data
    check                   Check service health
    unit                    Run unit tests
    integration            Run integration tests
    comprehensive          Run comprehensive test suite
    workflow               Test patient workflow
    api                    Test API endpoints
    speech                 Test speech-to-text service
    twilio                 Test Twilio integration
    all                    Run all tests
    report                 Generate test report
    help                   Show this help message

Examples:
    $0 setup --with-test-data
    $0 check
    $0 all
    $0 workflow
    $0 report

EOF
}

# Main script logic
case "${1:-help}" in
    "setup")
        check_services
        setup_test_environment "$2"
        ;;
    "check")
        check_services
        ;;
    "unit")
        check_services
        run_unit_tests
        ;;
    "integration")
        check_services
        run_integration_tests
        ;;
    "comprehensive")
        check_services
        run_comprehensive_tests
        ;;
    "workflow")
        check_services
        test_patient_workflow
        ;;
    "api")
        check_services
        test_api_endpoints
        ;;
    "speech")
        check_services
        test_speech_service
        ;;
    "twilio")
        check_services
        test_twilio_integration
        ;;
    "all")
        check_services
        log_info "Running complete test suite..."
        run_unit_tests
        run_integration_tests
        test_api_endpoints
        test_speech_service
        test_twilio_integration
        test_patient_workflow
        run_comprehensive_tests
        generate_test_report
        log_success "All tests completed!"
        ;;
    "report")
        generate_test_report
        ;;
    "help"|*)
        show_help
        ;;
esac
