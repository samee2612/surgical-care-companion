@echo off
REM TKA Voice Agent - Windows Component Testing Script
REM This script tests all components in isolation and integration

setlocal enabledelayedexpansion

REM Simple text markers (no color codes for better compatibility)
set "SUCCESS=[SUCCESS]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"
set "INFO=[INFO]"

echo ==========================================
echo TKA Voice Agent - Component Testing
echo ==========================================
echo.

REM Test configuration
set "BACKEND_URL=http://localhost:8000"
set "NGROK_URL="

REM Try to get ngrok URL
for /f "tokens=*" %%i in ('curl -s http://localhost:4040/api/tunnels 2^>nul ^| jq -r ".tunnels[0].public_url" 2^>nul') do set "NGROK_URL=%%i"

echo 📋 Test Configuration:
echo   • Backend URL: %BACKEND_URL%
if defined NGROK_URL (
    echo   • ngrok URL: %NGROK_URL%
) else (
    echo   • ngrok URL: Not available
)
echo.

REM Function to test service health
:test_service_health
set "service_name=%~1"
set "url=%~2"
set "expected_status=%~3"
if "%expected_status%"=="" set "expected_status=200"

echo %PURPLE%[TEST]%NC% Testing %service_name% health

for /f "tokens=*" %%i in ('curl -s -o nul -w "%%{http_code}" "%url%" 2^>nul') do set "response=%%i"

if "%response%"=="%expected_status%" (
    echo %GREEN%✅ %service_name% is healthy ^(HTTP %response%^)%NC%
    exit /b 0
) else (
    echo %RED%❌ %service_name% is unhealthy ^(HTTP %response%^)%NC%
    exit /b 1
)

REM Test Docker services
echo %BLUE%🐳 Testing Docker Services%NC%
echo ----------------------------------------

docker ps --format "table {{.Names}}" | findstr /r "tka_" >nul
if %errorlevel%==0 (
    echo %GREEN%✅ TKA Docker services are running%NC%
    docker ps --format "table {{.Names}}\t{{.Status}}" | findstr /r "tka_"
) else (
    echo %RED%❌ TKA Docker services are not running%NC%
    echo Run: docker-compose up -d
    goto :summary
)
echo.

REM Test PostgreSQL
echo %BLUE%🗄️ Testing PostgreSQL Database%NC%
echo ----------------------------------------

docker exec tka_postgres pg_isready -U user -d tka_voice >nul 2>&1
if %errorlevel%==0 (
    echo %GREEN%✅ PostgreSQL database is accessible%NC%
) else (
    echo %RED%❌ PostgreSQL database is not accessible%NC%
)
echo.

REM Test Redis
echo %BLUE%🔄 Testing Redis Cache%NC%
echo ----------------------------------------

docker exec tka_redis redis-cli ping >nul 2>&1
if %errorlevel%==0 (
    echo %GREEN%✅ Redis is responding to ping%NC%
    
    REM Test basic operations
    docker exec tka_redis redis-cli set test_key "test_value" >nul 2>&1
    for /f "tokens=*" %%i in ('docker exec tka_redis redis-cli get test_key 2^>nul') do set "redis_value=%%i"
    
    if "!redis_value!"=="test_value" (
        echo %GREEN%✅ Redis read/write operations working%NC%
        docker exec tka_redis redis-cli del test_key >nul 2>&1
    ) else (
        echo %RED%❌ Redis read/write operations failed%NC%
    )
) else (
    echo %RED%❌ Redis is not responding%NC%
)
echo.

REM Test Backend API
echo %BLUE%🔧 Testing Backend API%NC%
echo ----------------------------------------

REM Test health endpoint
curl -s "%BACKEND_URL%/health" | jq -e ".status == \"healthy\"" >nul 2>&1
if %errorlevel%==0 (
    echo %GREEN%✅ Health endpoint is working%NC%
) else (
    echo %RED%❌ Health endpoint failed%NC%
)

REM Test API docs
for /f "tokens=*" %%i in ('curl -s -o nul -w "%%{http_code}" "%BACKEND_URL%/docs" 2^>nul') do set "docs_response=%%i"
if "%docs_response%"=="200" (
    echo %GREEN%✅ API documentation is accessible%NC%
) else (
    echo %YELLOW%⚠️ API documentation not accessible%NC%
)

REM Test Twilio status
curl -s "%BACKEND_URL%/api/v1/calls/twilio-status" | jq -e ".configured" >nul 2>&1
if %errorlevel%==0 (
    echo %GREEN%✅ Twilio service status endpoint working%NC%
) else (
    echo %YELLOW%⚠️ Twilio service status endpoint not configured%NC%
)
echo.

REM Test Twilio Webhooks
echo %BLUE%📞 Testing Twilio Webhooks%NC%
echo ----------------------------------------

REM Test voice webhook
curl -s -w "%%{http_code}" -o webhook_response.xml ^
    -X POST "%BACKEND_URL%/api/v1/twilio/voice-webhook/test_session" ^
    -H "Content-Type: application/x-www-form-urlencoded" ^
    -d "CallSid=CAtest123&From=%%2B1234567890&To=%%2B18776589089&CallStatus=in-progress" 2>nul | findstr "200" >nul

if %errorlevel%==0 (
    findstr "<Response>" webhook_response.xml >nul 2>&1
    if !errorlevel!==0 (
        echo %GREEN%✅ Voice webhook returns valid TwiML%NC%
    ) else (
        echo %RED%❌ Voice webhook response is not valid TwiML%NC%
    )
) else (
    echo %RED%❌ Voice webhook failed%NC%
)

REM Test status callback
for /f "tokens=*" %%i in ('curl -s -o nul -w "%%{http_code}" -X POST "%BACKEND_URL%/api/v1/twilio/status-callback" -H "Content-Type: application/x-www-form-urlencoded" -d "CallSid=CAtest123&CallStatus=completed&CallDuration=120" 2^>nul') do set "callback_response=%%i"

if "%callback_response%"=="200" (
    echo %GREEN%✅ Status callback endpoint working%NC%
) else (
    echo %RED%❌ Status callback failed ^(HTTP %callback_response%^)%NC%
)
echo.

REM Test Speech Processing
echo %BLUE%🗣️ Testing Speech Processing%NC%
echo ----------------------------------------

echo {"session_id": "test_session_001", "transcription": "I am feeling much better today. My pain level is about 3 out of 10.", "confidence": 0.95} > speech_payload.json

curl -s -w "%%{http_code}" -o speech_response.json ^
    -X POST "%BACKEND_URL%/api/v1/twilio/process-speech" ^
    -H "Content-Type: application/json" ^
    -d @speech_payload.json 2>nul | findstr "200" >nul

if %errorlevel%==0 (
    jq -e ".response" speech_response.json >nul 2>&1
    if !errorlevel!==0 (
        echo %GREEN%✅ Speech processing endpoint working%NC%
        for /f "tokens=*" %%i in ('jq -r ".response" speech_response.json 2^>nul') do (
            set "ai_response=%%i"
            if defined ai_response (
                echo     AI Response: !ai_response:~0,100!...
            )
        )
    ) else (
        echo %RED%❌ Speech processing response invalid%NC%
    )
) else (
    echo %RED%❌ Speech processing failed%NC%
)
echo.

REM Test ngrok
echo %BLUE%🌐 Testing ngrok Tunnel%NC%
echo ----------------------------------------

if defined NGROK_URL (
    for /f "tokens=*" %%i in ('curl -s -o nul -w "%%{http_code}" "%NGROK_URL%/health" 2^>nul') do set "ngrok_health=%%i"
    
    if "!ngrok_health!"=="200" (
        echo %GREEN%✅ ngrok tunnel is working ^(%NGROK_URL%^)%NC%
        echo     Use this URL in Twilio Console: %NGROK_URL%/api/v1/twilio/voice-webhook/
    ) else (
        echo %RED%❌ ngrok tunnel not working ^(HTTP !ngrok_health!^)%NC%
    )
) else (
    echo %YELLOW%⚠️ ngrok URL not available - tunnel may not be running%NC%
    echo     Start ngrok with: ngrok http 8000
)
echo.

:summary
echo %BLUE%📊 Test Summary%NC%
echo ----------------------------------------
echo.
echo %GREEN%✅ Tests completed!%NC%
echo.
echo 📋 Next steps:
if defined NGROK_URL (
    echo   1. Configure Twilio webhook: %NGROK_URL%/api/v1/twilio/voice-webhook/
) else (
    echo   1. Start ngrok: ngrok http 8000
    echo   2. Get ngrok URL and configure Twilio webhook
)
echo   2. Test real call: curl -X POST %BACKEND_URL%/api/v1/calls/initiate
echo   3. Monitor logs: docker-compose logs -f backend
echo   4. View API docs: %BACKEND_URL%/docs
echo.

REM Cleanup
if exist webhook_response.xml del webhook_response.xml
if exist speech_payload.json del speech_payload.json
if exist speech_response.json del speech_response.json

pause
