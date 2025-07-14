# TKA Voice Agent - Complete Setup Guide

This guide provides step-by-step instructions to set up and run the complete TKA Voice Agent system with Twilio integration.

## 📋 System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Docker**: Latest version with Docker Compose
- **Git**: For cloning the repository
- **ngrok**: For webhook testing (development)

## 🔧 Prerequisites Setup

### 1. Install Required Software

**Windows:**
```powershell
# Install Python 3.11+
winget install Python.Python.3.11

# Install Node.js 18+
winget install OpenJS.NodeJS

# Install Docker Desktop
winget install Docker.DockerDesktop

# Install Git
winget install Git.Git
```

**macOS:**
```bash
# Install using Homebrew
brew install python@3.11 node docker git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 nodejs npm docker.io docker-compose git
```

### 2. Install ngrok (for development)
```bash
# Download from https://ngrok.com/download
# Or install via package manager
npm install -g ngrok
```

## 🏗️ Project Setup

### Step 1: Clone and Navigate to Repository
```bash
git clone <repository-url>
cd surgical-care-companion
```

### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your actual values
# See "Environment Variables Setup" section below
```

### Step 3: Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Frontend (if exists):**
```bash
# Note: Frontend appears to be missing from current structure
# You may need to create it or use a different UI
```

### Step 4: Start Infrastructure Services
```bash
# Start PostgreSQL, Redis, and pgAdmin
docker-compose up -d postgres redis pgadmin
```

### Step 5: Database Setup
```bash
# Make setup script executable (Linux/macOS)
chmod +x scripts/setup_database.sh

# Run database setup
./scripts/setup_database.sh

# Or manually:
cd backend
python -m alembic upgrade head
```

### Step 6: Start the Backend Service
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔑 Environment Variables Setup

### Required External Services

#### 1. Twilio Setup
1. **Create Account**: Go to [twilio.com](https://twilio.com) and sign up
2. **Get Credentials**: From Twilio Console Dashboard:
   - `TWILIO_ACCOUNT_SID`: Found on dashboard
   - `TWILIO_AUTH_TOKEN`: Found on dashboard (click to reveal)
3. **Buy Phone Number**: 
   - Go to Phone Numbers → Manage → Buy a number
   - Choose a voice-enabled number
   - Set `TWILIO_PHONE_NUMBER=+1234567890`

#### 2. Google Gemini API Setup
1. **Google Cloud Console**: Go to [console.cloud.google.com](https://console.cloud.google.com)
2. **Enable API**: Enable the Generative AI API
3. **Create API Key**: Go to APIs & Services → Credentials
4. **Set Variable**: `GEMINI_API_KEY=your_api_key_here`

#### 3. ngrok Setup (Development)
1. **Create Account**: Go to [ngrok.com](https://ngrok.com)
2. **Get Auth Token**: From dashboard
3. **Set Variable**: `NGROK_AUTHTOKEN=your_token_here`

#### 4. Email Setup (Optional)
For notifications, configure SMTP:
- Gmail: Use App Passwords
- `SMTP_USER=your_email@gmail.com`
- `SMTP_PASSWORD=your_app_password`

### Complete .env File
```bash
# Copy from .env.example and update these values:

# CRITICAL - Must be updated:
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-ngrok-url.com
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional - Update for production:
SECRET_KEY=your-very-secure-secret-key-min-32-characters
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Leave as default for development:
DATABASE_URL=postgresql://user:password@localhost:5432/tka_voice
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
DEBUG=true
```

## 🚀 Running the System

### Development Mode

#### 1. Start Infrastructure
```bash
# Start databases
docker-compose up -d postgres redis pgadmin

# Verify services are running
docker-compose ps
```

#### 2. Setup ngrok for Webhooks
```bash
# In a separate terminal
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update .env file: TWILIO_WEBHOOK_URL=https://abc123.ngrok.io
```

#### 3. Start Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Configure Twilio Webhooks
In Twilio Console:
1. Go to Phone Numbers → Manage → Active numbers
2. Click your phone number
3. Set webhook URL: `https://your-ngrok-url.com/api/v1/twilio/voice-webhook/{CallSid}`

### Production Mode
```bash
# Use Docker Compose for full deployment
docker-compose up -d

# Or build and run individually
docker-compose up -d postgres redis
docker-compose up backend
```

## 🧪 Testing the System

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. API Documentation
Visit: http://localhost:8000/docs

### 3. Database Administration
Visit: http://localhost:5050
- Email: admin@tka.com
- Password: admin

### 4. Test Call Initiation
```bash
curl -X POST "http://localhost:8000/api/v1/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test_patient_001",
    "call_session_id": "test_session_001",
    "call_type": "followup"
  }'
```

### 5. Check Twilio Status
```bash
curl http://localhost:8000/api/v1/calls/twilio-status
```

## 📁 Repository Structure Overview

```
surgical-care-companion/
├── .env.example              # Environment variables template
├── .env                      # Your actual environment variables (create this)
├── docker-compose.yml        # Multi-service Docker setup
├── README.md                 # Basic project info
│
├── backend/                  # Main FastAPI application
│   ├── api/                  # API endpoint definitions
│   │   ├── calls.py          # Call management endpoints
│   │   ├── patients.py       # Patient management
│   │   ├── twilio_webhooks.py # Twilio webhook handlers
│   │   └── voice_chat.py     # AI chat endpoints
│   │
│   ├── services/             # Business logic services
│   │   ├── call_service.py   # Call orchestration
│   │   ├── twilio_service.py # Twilio integration
│   │   ├── speech_to_text.py # Audio transcription
│   │   ├── voice_chat.py     # AI conversation
│   │   └── notification_service.py # Alerts & notifications
│   │
│   ├── database/             # Database models and connection
│   ├── config.py             # Application configuration
│   ├── main.py               # FastAPI application entry point
│   └── requirements.txt      # Python dependencies
│
├── docs/                     # Documentation
├── scripts/                  # Setup and utility scripts
└── tmp_audio/               # Temporary audio file storage
```

## 🔄 Complete Workflow

### 1. System Initialization
1. **Infrastructure**: PostgreSQL + Redis start via Docker
2. **Database**: Tables created via Alembic migrations
3. **Backend**: FastAPI server starts on port 8000
4. **Webhooks**: ngrok exposes local server to internet
5. **Twilio**: Configured to send webhooks to ngrok URL

### 2. Call Flow Process
1. **Initiate Call**: POST to `/api/v1/calls/initiate`
2. **Twilio Places Call**: Uses provided phone number
3. **Call Answered**: Webhook received at `/api/v1/twilio/voice-webhook/{session_id}`
4. **Generate Greeting**: TwiML response with initial message
5. **Audio Streaming**: Real-time audio sent via WebSocket
6. **Speech Processing**: Audio → Text via Whisper
7. **AI Response**: Text → AI Response via Gemini
8. **TwiML Generation**: AI Response → TwiML for Twilio
9. **Clinical Analysis**: Extract pain levels, concerns, etc.
10. **Alert Generation**: High-priority items trigger notifications
11. **Call Completion**: Summary generation and storage

### 3. Data Flow
```
Patient Phone ↔ Twilio Cloud ↔ ngrok ↔ FastAPI Backend
                                        ├─ Speech-to-Text
                                        ├─ AI Chat Service
                                        ├─ Database Storage
                                        └─ Notification System
```

## 🚨 Troubleshooting

### Common Issues

#### "Twilio credentials not configured"
- Check `.env` file exists and has correct values
- Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

#### "Database connection failed"
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database URL in `.env`

#### "Webhooks not receiving"
- Verify ngrok is running and HTTPS URL is correct
- Check Twilio webhook configuration
- Ensure backend is accessible from internet

#### "Import errors"
- Install requirements: `pip install -r backend/requirements.txt`
- Check Python version: `python --version`

#### "Call not initiating"
- Verify phone number format (+1234567890)
- Check Twilio account balance
- Confirm webhook URL is accessible

### Debug Commands
```bash
# Check service status
docker-compose ps

# View backend logs
docker-compose logs backend

# Test database connection
docker-compose exec postgres psql -U user -d tka_voice -c "SELECT 1;"

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check backend health
curl http://localhost:8000/health
```

## 🔒 Security Notes

- **Never commit `.env` file** - it's in `.gitignore`
- **Use strong secrets** in production
- **Enable Twilio signature validation** for webhooks
- **Use HTTPS** for all webhook endpoints
- **Implement proper authentication** for API endpoints

## 📚 Next Steps

1. **Set up monitoring**: Add logging and metrics
2. **Implement authentication**: Secure API endpoints
3. **Add frontend**: Create React dashboard
4. **Scale services**: Use load balancers and multiple instances
5. **Add tests**: Write comprehensive test suite
6. **Deploy to cloud**: Use AWS/GCP/Azure for production

---

This guide should get you up and running with the complete TKA Voice Agent system. For questions or issues, refer to the troubleshooting section or check the API documentation at http://localhost:8000/docs.
