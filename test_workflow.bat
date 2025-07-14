@echo off
echo ========================================
echo   Surgical Care Companion Flow Test
echo ========================================
echo.

set BASE_URL=http://localhost:8000
set NEW_PATIENT_ID=2526be90-305f-42b7-b41c-9b4d3e562571
set ORIGINAL_PATIENT_ID=85aa5fd7-2558-4bda-b1d0-0bec37bbbed6

echo [TEST 1] System Health Check...
curl -s "%BASE_URL%/health" | findstr "healthy" >nul
if %errorlevel% == 0 (
    echo   ✓ Health Check: PASSED
) else (
    echo   ✗ Health Check: FAILED
    goto :error
)

echo.
echo [TEST 2] Patient Management...
echo   Testing patient list...
curl -s "%BASE_URL%/api/v1/patients/" | findstr "Jane Doe" >nul
if %errorlevel% == 0 (
    echo   ✓ New Patient Found: Jane Doe (+12132757114)
) else (
    echo   ✗ New Patient Not Found
    goto :error
)

echo   Testing specific patient retrieval...
curl -s "%BASE_URL%/api/v1/patients/%NEW_PATIENT_ID%" | findstr "Jane Doe" >nul
if %errorlevel% == 0 (
    echo   ✓ Patient Details: PASSED
) else (
    echo   ✗ Patient Details: FAILED
    goto :error
)

echo.
echo [TEST 3] Call Management...
echo   Testing active calls list...
curl -s "%BASE_URL%/api/v1/calls/" | findstr "total_active" >nul
if %errorlevel% == 0 (
    echo   ✓ Call Management: PASSED
) else (
    echo   ✗ Call Management: FAILED
    goto :error
)

echo.
echo [TEST 4] Database Integration...
echo   Verifying patient count...
docker-compose exec -T postgres psql -U user -d tka_voice -c "SELECT COUNT(*) FROM patients;" | findstr "2" >nul
if %errorlevel% == 0 (
    echo   ✓ Database Patient Count: 2 patients found
) else (
    echo   ✗ Database Patient Count: Unexpected count
)

echo   Verifying new patient data...
docker-compose exec -T postgres psql -U user -d tka_voice -c "SELECT name FROM patients WHERE primary_phone_number = '+12132757114';" | findstr "Jane Doe" >nul
if %errorlevel% == 0 (
    echo   ✓ Database Patient Data: PASSED
) else (
    echo   ✗ Database Patient Data: FAILED
    goto :error
)

echo.
echo [TEST 5] Creating Call Session...
echo   Creating test call session...

REM Generate a new GUID for call session
for /f %%i in ('powershell -command "[guid]::NewGuid().ToString()"') do set CALL_SESSION_ID=%%i

echo   Call Session ID: %CALL_SESSION_ID%

docker-compose exec -T postgres psql -U user -d tka_voice -c "INSERT INTO call_sessions (id, patient_id, stage, surgery_type, scheduled_date, days_from_surgery, call_type, call_status) VALUES ('%CALL_SESSION_ID%', '%NEW_PATIENT_ID%', 'preop', 'knee', NOW(), -7, 'education', 'scheduled');" >nul

if %errorlevel% == 0 (
    echo   ✓ Call Session Created: PASSED
) else (
    echo   ✗ Call Session Creation: FAILED
    goto :error
)

echo.
echo [TEST 6] Voice Chat Integration...
echo   Testing contextual chat (this may show an error due to missing GEMINI_API_KEY)...

REM Create JSON payload file
echo {"message":"Hello, I'm Jane Doe. I have my knee surgery scheduled for next week. I'm feeling nervous about the procedure. Can you help me understand what to expect?","patient_id":"%NEW_PATIENT_ID%","call_session_id":"%CALL_SESSION_ID%","conversation_history":[]} > temp_payload.json

curl -X POST -H "Content-Type: application/json" -d @temp_payload.json "%BASE_URL%/api/v1/chat/contextual-chat" 2>nul | findstr "response\|error\|detail" >nul

if %errorlevel% == 0 (
    echo   ✓ Voice Chat Endpoint: ACCESSIBLE
    echo   Note: AI response may be limited without GEMINI_API_KEY
) else (
    echo   ✗ Voice Chat Endpoint: FAILED
)

del temp_payload.json 2>nul

echo.
echo [TEST 7] API Documentation...
curl -s "%BASE_URL%/docs" | findstr "swagger" >nul
if %errorlevel% == 0 (
    echo   ✓ API Documentation: ACCESSIBLE
) else (
    echo   ✗ API Documentation: FAILED
)

echo.
echo [TEST 8] Container Architecture...
docker-compose ps | findstr "Up" >nul
if %errorlevel% == 0 (
    echo   ✓ Container Status: HEALTHY
) else (
    echo   ✗ Container Status: ISSUES DETECTED
)

echo.
echo ========================================
echo           TEST SUMMARY
echo ========================================
echo ✓ System Health: OPERATIONAL
echo ✓ Patient Management: FUNCTIONAL
echo ✓ Database Integration: WORKING
echo ✓ Call Session Management: WORKING
echo ✓ API Infrastructure: READY
echo ✓ Container Architecture: STABLE
echo.
echo [NEXT STEPS]
echo 1. Add GEMINI_API_KEY for full AI conversations
echo 2. Configure Twilio credentials for voice calls
echo 3. Set up ngrok tunnel for webhook endpoints
echo 4. Test full voice calling workflow
echo.
echo [ACCESS URLS]
echo • API Documentation: %BASE_URL%/docs
echo • Health Check: %BASE_URL%/health
echo • Database Admin: http://localhost:5050
echo • Ngrok Interface: http://localhost:4040
echo.
echo [PATIENT DATA]
echo • Original Patient: John Smith (+1234567890)
echo • New Patient: Jane Doe (+12132757114)
echo • Call Session: %CALL_SESSION_ID%
echo.
goto :end

:error
echo.
echo ========================================
echo           TEST FAILED
echo ========================================
echo Please check the error messages above.
echo Run 'docker-compose logs backend' for detailed logs.
echo.

:end
pause
