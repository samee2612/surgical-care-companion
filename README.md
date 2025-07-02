# TKA Voice Agent System

An AI-powered voice agent for post-surgical patient monitoring, specifically designed for Total Knee Arthroplasty (TKA) recovery management.

## 🏥 Project Overview

This system automates post-surgical follow-up calls using:
- **Speech-to-Text**: Whisper for patient voice transcription
- **LLM Processing**: Google Gemini 2.5 Flash for clinical analysis
- **Text-to-Speech**: Coqui TTS for natural responses
- **Telephony**: Twilio Voice API for automated calls

## 🏗️ System Architecture

The system follows a 5-phase workflow:
1. **Patient Enrollment** - Clinical admin enrolls patients
2. **Scheduled Call Execution** - Automated outbound calls
3. **Live Voice Conversation** - Real-time AI-powered interactions
4. **Data Processing & Alerting** - Clinical rule evaluation
5. **Clinical Notification** - Alert delivery to medical staff

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd tka-voice-agent
```

2. **Backend Setup**
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

3. **Frontend Setup**
```bash
cd frontend
npm install
cd ..
```

4. **Start Services**
```bash
docker-compose up -d
```

5. **Initialize Database**
```bash
python scripts/setup_db.py
python scripts/seed_data.py
```

## 📋 API Documentation

- Backend API: http://localhost:8000/docs
- Frontend App: http://localhost:3000

## 🔧 Configuration

Required environment variables:
- `GEMINI_API_KEY` - Google Gemini API key
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `DATABASE_URL` - PostgreSQL connection string

## 📁 Project Structure

```
tka-voice-agent/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── tests/           # Test suites
├── scripts/         # Setup scripts
└── docs/           # Documentation
```

## 🧪 Testing

```bash
# Backend tests
pytest tests/backend/

# Frontend tests
cd frontend && npm test
```

## 📊 Features

- ✅ Patient enrollment and management
- ✅ Automated call scheduling
- ✅ Real-time voice processing
- ✅ Clinical decision support
- ✅ Alert management
- ✅ HIPAA-compliant data handling

## 🔒 Security & Compliance

- HIPAA-compliant data encryption
- Secure API authentication
- Audit logging for all patient interactions
- Role-based access control

## 📞 Support

For technical support or questions, please refer to the documentation in the `docs/` directory. 