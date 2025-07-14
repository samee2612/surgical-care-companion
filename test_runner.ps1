# Surgical Care Companion - Comprehensive Testing Script (PowerShell)
# ================================================================
# This script provides easy access to all testing workflows
# for the Surgical Care Companion system on Windows.

param(
    [Parameter(Position=0)]
    [string]$Action = "help",
    
    [Parameter(Position=1)]
    [string]$Option = ""
)

# Configuration
$BaseURL = "http://localhost:8000"
$DockerComposeFile = "docker-compose.yml"

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Services {
    Write-Info "Checking service availability..."
    
    # Check if Docker Compose services are running
    $services = docker-compose ps
    if (-not ($services -match "Up")) {
        Write-Error "Docker Compose services are not running!"
        Write-Info "Starting services..."
        docker-compose up -d
        Start-Sleep -Seconds 10
    }
    
    # Check backend health
    try {
        $response = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get -TimeoutSec 5
        Write-Success "Backend service is healthy"
    }
    catch {
        Write-Error "Backend service is not responding"
        exit 1
    }
    
    # Check database connectivity
    try {
        $dbCheck = docker-compose exec -T postgres pg_isready -U user 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database is ready"
        }
        else {
            Write-Error "Database is not ready"
            exit 1
        }
    }
    catch {
        Write-Error "Database check failed"
        exit 1
    }
}

function Initialize-TestEnvironment {
    param([string]$WithTestData)
    
    Write-Info "Setting up test environment..."
    
    # Run database migrations
    Write-Info "Running database migrations..."
    docker-compose exec -T backend python scripts/run_migrations.py
    
    # Initialize test data if needed
    if ($WithTestData -eq "--with-test-data") {
        Write-Info "Initializing test data..."
        docker-compose exec -T backend python scripts/setup_education_test.py
    }
    
    Write-Success "Test environment ready"
}

function Invoke-UnitTests {
    Write-Info "Running unit tests..."
    docker-compose exec -T backend python -m pytest tests/test_unit.py -v --tb=short
    Write-Success "Unit tests completed"
}

function Invoke-IntegrationTests {
    Write-Info "Running integration tests..."
    docker-compose exec -T backend python -m pytest tests/test_integration.py -v --tb=short
    Write-Success "Integration tests completed"
}

function Invoke-ComprehensiveTests {
    Write-Info "Running comprehensive test suite..."
    python test_comprehensive.py --run-all --base-url $BaseURL
    Write-Success "Comprehensive tests completed"
}

function Test-PatientWorkflow {
    Write-Info "Testing complete patient workflow..."
    
    # Create test patient data
    $testPatient = @{
        name = "Test Patient Workflow"
        primary_phone_number = "+12132757114"
        surgery_date = "2025-08-15T09:00:00Z"
        primary_physician_id = "test-physician-id"
    } | ConvertTo-Json
    
    try {
        Write-Info "Creating test patient..."
        $patientResponse = Invoke-RestMethod -Uri "$BaseURL/api/patients/" `
            -Method Post `
            -ContentType "application/json" `
            -Body $testPatient
        
        Write-Success "Test patient created successfully"
        $patientId = $patientResponse.id
        
        # Test call initiation
        Write-Info "Testing call initiation..."
        $callData = @{
            patient_id = $patientId
            call_type = "education"
        } | ConvertTo-Json
        
        $callResponse = Invoke-RestMethod -Uri "$BaseURL/api/calls/initiate" `
            -Method Post `
            -ContentType "application/json" `
            -Body $callData
        
        if ($callResponse.call_session_id) {
            Write-Success "Call initiated successfully"
        }
        else {
            Write-Error "Call initiation failed"
        }
    }
    catch {
        Write-Error "Patient workflow test failed: $($_.Exception.Message)"
    }
}

function Test-ApiEndpoints {
    Write-Info "Testing API endpoints..."
    
    try {
        # Test health endpoints
        $healthResponse = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get
        Write-Success "Main health endpoint OK"
        
        $apiHealthResponse = Invoke-RestMethod -Uri "$BaseURL/api/health" -Method Get
        Write-Success "API health endpoint OK"
        
        # Test API endpoints
        $patientsResponse = Invoke-RestMethod -Uri "$BaseURL/api/patients/" -Method Get
        Write-Success "Patients endpoint returning valid JSON"
        
        $staffResponse = Invoke-RestMethod -Uri "$BaseURL/api/clinical/staff" -Method Get
        Write-Success "Clinical staff endpoint returning valid JSON"
    }
    catch {
        Write-Error "API endpoint test failed: $($_.Exception.Message)"
    }
}

function Test-SpeechService {
    Write-Info "Testing speech-to-text service..."
    
    try {
        $speechHealthResponse = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get -TimeoutSec 5
        Write-Success "Speech-to-text service is running"
        
        # Test with sample audio if available
        if (Test-Path "test\sample.wav") {
            Write-Info "Testing audio transcription..."
            # Note: PowerShell multipart form data is more complex
            Write-Warning "Audio transcription test requires manual verification"
        }
        else {
            Write-Warning "No sample audio file found for testing"
        }
    }
    catch {
        Write-Warning "Speech-to-text service is not running"
    }
}

function Test-TwilioIntegration {
    Write-Info "Testing Twilio integration..."
    
    try {
        $webhookData = @{
            CallSid = "test123"
            From = "%2B12132757114"
            To = "%2B18776589089"
            CallStatus = "in-progress"
        }
        
        $body = ($webhookData.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
        
        $response = Invoke-RestMethod -Uri "$BaseURL/webhooks/twilio/voice" `
            -Method Post `
            -ContentType "application/x-www-form-urlencoded" `
            -Body $body
        
        Write-Success "Twilio webhook endpoint responding"
    }
    catch {
        Write-Error "Twilio webhook endpoint failed: $($_.Exception.Message)"
    }
}

function New-TestReport {
    Write-Info "Generating test report..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportFile = "test_report_$timestamp.txt"
    
    $report = @"
Surgical Care Companion - Test Report
=====================================
Generated: $(Get-Date)
Base URL: $BaseURL

Service Status:
$(docker-compose ps)

System Information:
PowerShell Version: $($PSVersionTable.PSVersion)
OS: $($env:OS)

"@
    
    $report | Out-File -FilePath $reportFile -Encoding UTF8
    Write-Success "Test report saved to $reportFile"
}

function Show-Help {
    @"
Surgical Care Companion - Testing Script (PowerShell)
====================================================

Usage: .\test_runner.ps1 [ACTION] [OPTION]

Actions:
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
    .\test_runner.ps1 setup --with-test-data
    .\test_runner.ps1 check
    .\test_runner.ps1 all
    .\test_runner.ps1 workflow
    .\test_runner.ps1 report

"@
}

# Main script logic
switch ($Action.ToLower()) {
    "setup" {
        Test-Services
        Initialize-TestEnvironment -WithTestData $Option
    }
    "check" {
        Test-Services
    }
    "unit" {
        Test-Services
        Invoke-UnitTests
    }
    "integration" {
        Test-Services
        Invoke-IntegrationTests
    }
    "comprehensive" {
        Test-Services
        Invoke-ComprehensiveTests
    }
    "workflow" {
        Test-Services
        Test-PatientWorkflow
    }
    "api" {
        Test-Services
        Test-ApiEndpoints
    }
    "speech" {
        Test-Services
        Test-SpeechService
    }
    "twilio" {
        Test-Services
        Test-TwilioIntegration
    }
    "all" {
        Test-Services
        Write-Info "Running complete test suite..."
        Invoke-UnitTests
        Invoke-IntegrationTests
        Test-ApiEndpoints
        Test-SpeechService
        Test-TwilioIntegration
        Test-PatientWorkflow
        Invoke-ComprehensiveTests
        New-TestReport
        Write-Success "All tests completed!"
    }
    "report" {
        New-TestReport
    }
    default {
        Show-Help
    }
}
