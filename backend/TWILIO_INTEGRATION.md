# Twilio Voice Service Integration

This document describes the comprehensive Twilio voice service integration for the Surgical Care Companion system. The integration provides scalable, feature-rich voice calling capabilities with real-time speech processing and AI-powered conversation management.

## 🎯 Overview

The Twilio service handles:
- **Outbound call initiation** with custom payloads and context
- **Real-time audio streaming** for immediate transcription
- **TwiML generation** for dynamic conversation flow
- **Call status tracking** and webhook management
- **Speech-to-text processing** with streaming support
- **AI response generation** with contextual awareness
- **Clinical alert detection** and notification routing

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Call Service   │────│  Twilio Service  │────│  Twilio Cloud   │
│  (Orchestrator) │    │   (Voice API)    │    │   (Telephony)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────┴────────┐             │
         │              │                 │             │
         ▼              ▼                 ▼             ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Speech-to-    │    │   AI Chat        │    │   Webhook       │
│   Text Service  │    │   Service        │    │   Endpoints     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Features

### 1. Call Initiation
- Programmatic call initiation via REST API
- Custom payloads with patient context and conversation data
- Configurable call types (followup, enrollment, education)
- Phone number validation and formatting
- Webhook URL generation and management

### 2. Real-time Audio Processing
- WebSocket-based audio streaming from Twilio
- Continuous speech-to-text transcription
- Real-time clinical data extraction
- Immediate alert detection and routing

### 3. Dynamic Conversation Flow
- TwiML generation based on conversation context
- AI-powered response generation
- Adaptive questioning based on patient responses
- Fallback handling for unclear responses

### 4. Call Management
- Active call session tracking
- Call status monitoring and updates
- Conversation history maintenance
- Clinical data accumulation

### 5. Integration Points
- **Call Service**: Orchestrates the entire call workflow
- **Speech-to-Text**: Processes audio streams and recordings
- **AI Chat Service**: Generates contextual responses
- **Notification Service**: Handles clinical alerts and summaries

## 📝 Configuration

### Environment Variables

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-ngrok-url.com

# AI Services
GEMINI_API_KEY=your_gemini_api_key
WHISPER_MODEL=base

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/surgical_care
REDIS_URL=redis://localhost:6379

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Twilio Setup

1. **Create Twilio Account**: Sign up at [twilio.com](https://twilio.com)
2. **Get Phone Number**: Purchase a voice-enabled phone number
3. **Configure Webhooks**: Set webhook URLs in Twilio console
4. **Test Connection**: Use the provided endpoints to verify setup

## 🔌 API Endpoints

### Call Management

```http
POST /api/v1/calls/initiate
Content-Type: application/json

{
  "patient_id": "patient_001",
  "call_session_id": "session_20240101_120000",
  "call_type": "followup"
}
```

```http
GET /api/v1/calls/status/{call_session_id}
```

```http
GET /api/v1/calls/transcripts/{call_session_id}
```

### Twilio Webhooks (Internal)

```http
POST /api/v1/twilio/voice-webhook/{call_session_id}
```

```http
WebSocket /api/v1/twilio/audio-stream/{call_session_id}
```

```http
POST /api/v1/twilio/status-callback/{call_session_id}
```

## 🔄 Call Flow

### 1. Call Initiation
```python
# Example call initiation
call_result = await call_service.initiate_patient_call(
    patient_id="patient_001",
    call_session_id="session_123",
    call_type="followup"
)
```

### 2. Webhook Handling
1. **Twilio places call** → Status callback (initiated)
2. **Call answered** → Voice webhook called
3. **Generate greeting** → TwiML returned to Twilio
4. **Patient speaks** → Audio stream processed
5. **AI responds** → New TwiML generated
6. **Call ends** → Status callback (completed)

### 3. Speech Processing
```python
# Real-time speech processing
transcription = await stt_service.transcribe_stream(
    audio_data=audio_chunk,
    session_id=call_session_id
)

# AI response generation
response = await chat_service.generate_contextual_response(
    user_message=transcription.text,
    system_prompt=context_prompt,
    context_metadata=call_context
)
```

## 🚨 Clinical Alerts

The system automatically detects and routes clinical alerts:

### Alert Types
- **High Pain Level**: Pain score ≥ 7
- **Patient Concerns**: Explicit concern mentions
- **Mobility Issues**: Movement difficulties
- **Wound Problems**: Incision site concerns
- **Medication Issues**: Compliance problems

### Alert Routing
- **Low Severity**: In-app notifications
- **Moderate**: Email + in-app
- **High**: Email + SMS + in-app
- **Urgent/Critical**: All channels + webhooks

## 📊 Monitoring and Analytics

### Call Metrics
- Active call count and status
- Call duration and completion rates
- Transcription accuracy and confidence
- AI response quality metrics

### Clinical Metrics
- Alert frequency by type and severity
- Patient response patterns
- Recovery progress indicators
- Care team response times

### System Health
- Twilio service connectivity
- Speech-to-text service availability
- AI service response times
- Webhook delivery success rates

## 🧪 Testing

### Development Testing
```bash
# Start the backend service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Use ngrok for webhook testing
ngrok http 8000

# Test call initiation
curl -X POST "http://localhost:8000/api/v1/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test_patient",
    "call_session_id": "test_session_123",
    "call_type": "followup"
  }'
```

### Webhook Testing
Use tools like [ngrok](https://ngrok.com) to expose your local development server:

```bash
ngrok http 8000
# Use the HTTPS URL as your TWILIO_WEBHOOK_URL
```

### Mock Patient Calls
The system includes mock responses for testing without actual phone calls:

```python
# See examples/twilio_service_example.py for comprehensive examples
python examples/twilio_service_example.py
```

## 🔒 Security Considerations

### Webhook Validation
- Implement Twilio signature validation
- Use HTTPS for all webhook endpoints
- Validate request sources and formats

### Data Protection
- Encrypt sensitive patient data
- Implement proper access controls
- Log and monitor all call activities

### Compliance
- HIPAA compliance for healthcare data
- Call recording consent and management
- Data retention and deletion policies

## 🚀 Deployment

### Docker Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}
      - TWILIO_WEBHOOK_URL=${TWILIO_WEBHOOK_URL}
```

### Production Considerations
- Use load balancers for webhook endpoints
- Implement webhook retry logic
- Set up monitoring and alerting
- Configure backup notification channels

## 🔧 Troubleshooting

### Common Issues

#### Call Not Initiating
- Check Twilio credentials
- Verify phone number format
- Confirm webhook URL accessibility

#### Audio Stream Issues
- Verify WebSocket connection
- Check audio codec compatibility
- Monitor stream data flow

#### Transcription Problems
- Validate audio quality
- Check speech-to-text service status
- Review confidence scores

#### AI Response Delays
- Monitor AI service performance
- Check API rate limits
- Verify context data quality

### Debug Endpoints
```http
GET /api/v1/calls/twilio-status
GET /api/v1/calls/analytics
GET /health
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Multiple backend instances with load balancing
- Shared session storage (Redis/Database)
- Distributed webhook handling

### Performance Optimization
- Connection pooling for database and Redis
- Async processing for long-running tasks
- Caching for frequently accessed data

### Cost Management
- Monitor Twilio usage and costs
- Implement call duration limits
- Optimize AI service usage

## 🤝 Contributing

When contributing to the Twilio service:

1. **Follow the existing patterns** for service integration
2. **Add comprehensive logging** for debugging
3. **Include error handling** for all external calls
4. **Write tests** for new functionality
5. **Update documentation** for any API changes

## 📚 Resources

- [Twilio Voice API Documentation](https://www.twilio.com/docs/voice)
- [TwiML Voice Reference](https://www.twilio.com/docs/voice/twiml)
- [Twilio Webhooks Guide](https://www.twilio.com/docs/usage/webhooks)
- [OpenAI Whisper Documentation](https://github.com/openai/whisper)
- [Google Gemini API Documentation](https://cloud.google.com/generative-ai)

---

For additional support or questions, please refer to the main project documentation or create an issue in the project repository.
