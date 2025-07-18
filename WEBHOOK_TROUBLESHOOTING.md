# Twilio Webhook "Application Error" Troubleshooting Guide

## Overview
This guide helps diagnose and fix "Application error" issues in your Twilio voice webhook implementation.

## Common Causes and Solutions

### 1. HTTP 500 Internal Server Error

**Problem:** Your FastAPI application returns a 500 error instead of valid TwiML.

**Immediate Actions:**
```bash
# Check your application logs
tail -f /var/log/your-app.log

# Or if running locally
python -m uvicorn main:app --reload --log-level debug
```

**Check for these issues:**
- Database connection failures
- Missing environment variables
- Import errors
- Timeout issues with external services

### 2. Processing Timeout (15 seconds)

**Problem:** Your webhook takes longer than 15 seconds to respond.

**Solutions:**
- Add timeout protection to external API calls
- Implement fallback responses
- Use async processing for heavy operations

**Code Example:**
```python
import asyncio

try:
    # Protect external API calls with timeout
    analysis = await asyncio.wait_for(
        gemini_service.analyze_conversation(transcript, messages),
        timeout=8.0  # 8 seconds max
    )
except asyncio.TimeoutError:
    # Use fallback analysis
    analysis = {"intent": "general", "urgency": "low"}
```

### 3. Invalid TwiML Response

**Problem:** Your application returns non-XML content to Twilio.

**Solutions:**
- Always return valid TwiML XML
- Use proper error handling in webhooks
- Validate TwiML before sending

**Code Example:**
```python
def _create_safe_twiml_response(message: str) -> str:
    """Create guaranteed valid TwiML response"""
    try:
        response = VoiceResponse()
        response.say(message)
        response.hangup()
        return str(response)
    except Exception:
        # Last resort - manually create valid TwiML
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{message}</Say><Hangup/></Response>'
```

### 4. Database Connection Issues

**Problem:** Database queries fail or timeout.

**Solutions:**
- Add connection pooling
- Implement retry logic
- Use connection health checks

**Code Example:**
```python
# Check database connection before processing
try:
    db.execute("SELECT 1")
except Exception as db_error:
    logger.error(f"Database connection failed: {db_error}")
    return _create_error_twiml("Service temporarily unavailable")
```

## Debugging Steps

### Step 1: Check Application Logs
```bash
# Look for these patterns in your logs:
grep -i "error\|exception\|timeout\|failed" /var/log/your-app.log

# Check for specific webhook errors:
grep -i "voice webhook" /var/log/your-app.log
```

### Step 2: Test Webhook Locally
```bash
# Run the debug script
cd backend
python test_webhook_debug.py

# Check the generated log file
cat webhook_debug.log
```

### Step 3: Monitor Response Times
```bash
# Add timing logs to your webhook
import time
start_time = time.time()
# ... your webhook code ...
duration = time.time() - start_time
logger.info(f"Webhook processed in {duration:.2f}s")
```

### Step 4: Use Twilio Debugger
1. Go to Twilio Console → Monitor → Debugger
2. Find your failed call
3. Check the webhook request/response details
4. Look for HTTP status codes and error messages

### Step 5: Test with Simple TwiML
Replace your webhook temporarily with a simple response:
```python
@router.post("/twilio/voice", response_class=PlainTextResponse)
async def simple_test_webhook(request: Request):
    """Simple test webhook"""
    response = VoiceResponse()
    response.say("Hello! This is a test call.")
    response.hangup()
    return str(response)
```

## Environment Variables Checklist

Ensure these are set:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token

# AI Services
GEMINI_API_KEY=your_gemini_key

# Application
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

## Performance Optimization

### 1. Reduce External API Calls
```python
# Cache frequently used data
@lru_cache(maxsize=100)
def get_patient_context(patient_id):
    # Cached patient data
    pass
```

### 2. Use Connection Pooling
```python
# In your database configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 3. Implement Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

## Monitoring and Alerting

### 1. Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    # Test database connection
    # Test external services
    # Return detailed health status
    pass
```

### 2. Metrics Collection
```python
import prometheus_client

webhook_duration = prometheus_client.Histogram(
    'webhook_processing_duration_seconds',
    'Time spent processing webhook requests'
)

@webhook_duration.time()
async def twilio_voice_webhook(...):
    # Your webhook code
    pass
```

### 3. Error Tracking
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

## Common Error Patterns

### Pattern 1: Gemini API Timeout
```
Error: Request to Gemini API timed out
Solution: Add timeout protection and fallback responses
```

### Pattern 2: Database Lock
```
Error: Database is locked
Solution: Use connection pooling and retry logic
```

### Pattern 3: Memory Issues
```
Error: Out of memory
Solution: Optimize conversation history storage
```

### Pattern 4: Import Errors
```
Error: ModuleNotFoundError
Solution: Check virtual environment and dependencies
```

## Quick Fix Checklist

- [ ] Check application logs for errors
- [ ] Verify database connectivity
- [ ] Test webhook with simple TwiML
- [ ] Monitor response times
- [ ] Check Twilio debugger
- [ ] Validate environment variables
- [ ] Test external API connections
- [ ] Review recent code changes
- [ ] Check system resources (CPU, memory)
- [ ] Verify network connectivity

## Production Deployment Checklist

- [ ] Use production database
- [ ] Configure proper logging
- [ ] Set up monitoring and alerting
- [ ] Use environment-specific configurations
- [ ] Implement proper error handling
- [ ] Add request/response logging
- [ ] Test with realistic load
- [ ] Set up backup webhook URL
- [ ] Configure SSL/TLS properly
- [ ] Document incident response procedures

## Emergency Response

If you're experiencing a production outage:

1. **Immediate**: Switch to backup webhook URL
2. **Quick Fix**: Deploy simple TwiML response
3. **Investigation**: Check logs and metrics
4. **Resolution**: Fix root cause and deploy
5. **Post-mortem**: Document lessons learned

## Contact Information

For urgent issues:
- Check Twilio Status: https://status.twilio.com/
- Twilio Support: https://support.twilio.com/
- Internal escalation: [Your team's contact info]
