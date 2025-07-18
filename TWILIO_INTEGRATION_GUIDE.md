# Surgical Care Companion - Complete Twilio TwiML Integration Flow

## 🎯 **Overview**

This document describes the complete flow for Twilio TwiML interactive voice calls with transcript processing, intent extraction, and conversation management.

## 📋 **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Patient Call  │───▶│  Twilio TwiML   │───▶│   FastAPI       │
│                 │    │   Webhooks      │    │   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◀───│  Conversation   │───▶│   Whisper STT   │
│   Database      │    │   Manager       │    │   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │◀───│  JSON Context   │───▶│  Gemini AI      │
│   Dashboard     │    │   Storage       │    │  Analysis       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 **Complete Call Flow**

### 1. **Call Initiation**
- Patient calls Twilio number
- Twilio sends webhook to `/webhooks/twilio/voice`
- System identifies patient by phone number
- Creates new conversation record

### 2. **Voice Interaction**
- TwiML plays greeting and asks questions
- Patient responds with voice
- Twilio records speech and sends RecordingURL
- System downloads and transcribes audio using Whisper

### 3. **AI Processing**
- Transcript sent to Gemini AI for analysis
- Extracts: intent, entities, sentiment, urgency
- Identifies symptoms, pain levels, concerns
- Generates recommended actions

### 4. **Context Management**
- Conversation history stored as JSON
- Previous context used for follow-up questions
- Intelligent conversation flow based on AI analysis

### 5. **Response Generation**
- System generates appropriate follow-up questions
- TwiML continues conversation or ends call
- Critical cases trigger immediate alerts

## 🗂️ **Database Schema**

### Conversations Table
```sql
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY,
    patient_id VARCHAR NOT NULL,
    call_sid VARCHAR UNIQUE,
    phone_number VARCHAR NOT NULL,
    call_direction VARCHAR,
    call_status VARCHAR,
    call_duration INTEGER,
    conversation_json JSONB,
    transcript TEXT,
    intent VARCHAR,
    entities JSONB,
    sentiment VARCHAR,
    urgency_level VARCHAR,
    symptoms JSONB,
    pain_level INTEGER,
    concerns JSONB,
    actions_required JSONB,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Conversation JSON Structure
```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "Hello! How are you feeling today?",
      "timestamp": "2025-01-17T10:00:00Z",
      "type": "greeting"
    },
    {
      "role": "user",
      "content": "I'm feeling some pain in my knee",
      "timestamp": "2025-01-17T10:00:30Z",
      "audio_url": "https://api.twilio.com/recording/123",
      "confidence": 0.95
    }
  ],
  "completed_actions": [],
  "follow_up_scheduled": false
}
```

## 📱 **Frontend Integration**

### Call Dashboard Features
- **Real-time call monitoring**
- **Conversation history viewer**
- **Urgency-based filtering**
- **Analytics and statistics**
- **Action management**

### Key Components
- `CallDashboard.tsx` - Main dashboard interface
- Real-time updates via API polling
- Conversation detail modal
- Urgency level indicators

## 🔧 **Setup Instructions**

### 1. Environment Configuration
```bash
# Required environment variables
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_phone_number
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql://harsh:harshpassword@localhost:5432/surgicalcare_db
```

### 2. Docker Deployment
```bash
# Start all services
./start.ps1   # Windows
./start.sh    # Linux/Mac

# Or manually
docker-compose up --build -d
```

### 3. Twilio Webhook Configuration
1. Install ngrok: `ngrok http 8000`
2. Set webhook URLs in Twilio Console:
   - Voice: `https://your-ngrok-url.ngrok.io/webhooks/twilio/voice`
   - SMS: `https://your-ngrok-url.ngrok.io/webhooks/twilio/sms`

## 🎯 **API Endpoints**

### Voice Webhook
- **POST** `/webhooks/twilio/voice`
- Handles TwiML voice interactions
- Processes recordings and DTMF input
- Returns TwiML responses

### SMS Webhook
- **POST** `/webhooks/twilio/sms`
- Handles SMS messages
- Analyzes text with Gemini AI
- Returns SMS responses

### Conversations API
- **GET** `/api/v1/conversations` - List conversations
- **GET** `/api/v1/conversations/{id}` - Get conversation details
- **GET** `/api/v1/conversations/stats` - Analytics
- **POST** `/api/v1/conversations/{id}/actions` - Mark actions complete

## 🧠 **AI Analysis Features**

### Gemini AI Processing
- **Intent Recognition**: pain_inquiry, wound_check, medication_question, emergency
- **Entity Extraction**: pain_level, symptoms, medications, activities
- **Sentiment Analysis**: positive, negative, neutral, anxious, distressed
- **Urgency Assessment**: low, medium, high, critical
- **Clinical Assessment**: Pain, wound status, mobility, medication compliance

### Sample Analysis Output
```json
{
  "intent": "pain_inquiry",
  "entities": {
    "pain_level": 7,
    "symptoms": ["swelling", "stiffness"],
    "medications": ["ibuprofen"],
    "concerns": ["increased pain at night"]
  },
  "sentiment": "anxious",
  "urgency_level": "medium",
  "clinical_assessment": {
    "pain_assessment": "Moderate to severe pain, concerning trend",
    "wound_status": "No specific wound concerns mentioned",
    "mobility_status": "Limited due to pain and stiffness",
    "medication_compliance": "Patient using over-the-counter pain relief"
  },
  "recommended_actions": [
    "Contact healthcare provider about pain management",
    "Consider prescription pain medication review",
    "Monitor for signs of infection"
  ],
  "requires_immediate_attention": false
}
```

## 📊 **Monitoring & Analytics**

### Dashboard Metrics
- Total calls processed
- Urgent cases requiring attention
- Average pain levels
- Sentiment distribution
- Completion rates

### Alert System
- Critical urgency cases highlighted
- Required actions tracked
- Follow-up recommendations
- Healthcare provider notifications

## 🔄 **Conversation Context Management**

### Context Persistence
- Previous conversation history loaded for each patient
- Context used to generate personalized responses
- Conversation flow adapts based on patient history

### Sample Context Usage
```javascript
// Previous context influences next questions
if (lastConversation.pain_level > 6) {
  askAboutPainMedication();
} else if (lastConversation.concerns.includes("wound")) {
  askAboutWoundHealing();
}
```

## 🚀 **Deployment Checklist**

- [ ] Environment variables configured
- [ ] Docker services running
- [ ] Database migrated
- [ ] Twilio webhooks configured
- [ ] Ngrok tunnel established
- [ ] Test calls working
- [ ] Frontend dashboard accessible
- [ ] AI analysis functioning

## 🧪 **Testing**

### Manual Testing
1. Call the Twilio number
2. Speak responses to questions
3. Check conversation in dashboard
4. Verify AI analysis results
5. Test SMS functionality

### Integration Testing
```bash
# Test voice webhook
curl -X POST http://localhost:8000/webhooks/twilio/voice \
  -d "From=+1234567890&CallSid=CA123"

# Test SMS webhook
curl -X POST http://localhost:8000/webhooks/twilio/sms \
  -d "From=+1234567890&Body=I have knee pain"
```

## 🎯 **Next Steps**

1. **Scale Implementation**: Add more conversation flows
2. **Advanced Analytics**: Implement reporting dashboards
3. **EHR Integration**: Connect with hospital systems
4. **Multi-language Support**: Add localization
5. **Mobile App**: Create companion mobile application

This implementation provides a complete, functional Twilio TwiML integration with AI-powered conversation management, ready for production use in healthcare settings.
