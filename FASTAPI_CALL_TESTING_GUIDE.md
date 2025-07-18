# FastAPI Call Testing Guide

## How to Test Twilio Calls Through Your FastAPI Backend

### Method 1: Using the Python Test Script

1. **Make sure your backend is running:**
   ```bash
   docker-compose up -d
   ```

2. **Run the test script:**
   ```bash
   python test_fastapi_call.py
   ```

### Method 2: Using FastAPI Interactive Docs (Swagger UI)

1. **Open your browser and go to:**
   ```
   http://localhost:8000/docs
   ```

2. **Find the "calls" section and click on POST `/api/v1/calls/test-call`**

3. **Click "Try it out" button**

4. **Enter the request body:**
   ```json
   {
     "to_number": "+12132757114"
   }
   ```

5. **Click "Execute"**

6. **Your phone should ring!**

### Method 3: Using curl Command

```bash
curl -X POST "http://localhost:8000/api/v1/calls/test-call" \
     -H "Content-Type: application/json" \
     -d '{
       "to_number": "+12132757114"
     }'
```

### Method 4: Using PowerShell Invoke-RestMethod

```powershell
$headers = @{'Content-Type' = 'application/json'}
$body = @{
    to_number = "+12132757114"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/calls/test-call" -Method POST -Headers $headers -Body $body
```

### Method 5: Using Postman

1. **Create a new POST request**
2. **URL:** `http://localhost:8000/api/v1/calls/test-call`
3. **Headers:** `Content-Type: application/json`
4. **Body (raw JSON):**
   ```json
   {
     "to_number": "+12132757114"
   }
   ```
5. **Send the request**

## Expected Response

When successful, you should get a response like:

```json
{
  "success": true,
  "call_sid": "CA1234567890abcdef1234567890abcdef",
  "status": "queued",
  "from": "+18776589089",
  "to": "+12132757114",
  "webhook_url": "https://bbd2b88f163a.ngrok-free.app/api/webhooks/twilio/voice",
  "message": "Call initiated to +12132757114"
}
```

## Troubleshooting

### Backend Not Running
- **Error:** Connection refused
- **Solution:** Start with `docker-compose up -d`

### Twilio Credentials Missing
- **Error:** "Missing Twilio credentials in environment variables"
- **Solution:** Check your `.env` file has:
  ```
  TWILIO_ACCOUNT_SID=AC3123f54e85931d681c837b9b16f653a1
  TWILIO_AUTH_TOKEN=6972474561a33d1f95f78b22950be343
  TWILIO_PHONE_NUMBER=+18776589089
  ```

### Webhook URL Issues
- **Error:** Call connects but no voice response
- **Solution:** Make sure ngrok is running and webhook URL is correct

### Package Missing
- **Error:** "Twilio package not installed"
- **Solution:** Install in your backend container:
  ```bash
  docker-compose exec backend pip install twilio
  ```

## What Happens When You Test

1. **API Call:** Your request goes to FastAPI backend
2. **Twilio Call:** Backend uses Twilio API to initiate call
3. **Phone Rings:** Your phone (+12132757114) receives the call
4. **Webhook Triggered:** When you answer, Twilio calls your webhook
5. **Voice Response:** Your backend returns TwiML for interactive voice
6. **Interactive Session:** You can speak or press keys to interact

## Advanced Options

You can also specify custom parameters:

```json
{
  "to_number": "+12132757114",
  "from_number": "+18776589089",
  "webhook_url": "https://your-custom-url.com/webhook"
}
```

This gives you full control over the call parameters!
