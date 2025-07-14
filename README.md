# Surgical Care Companion - AI-Powered TKA Patient Monitoring System

An intelligent voice agent system for automated post-surgical patient monitoring, specifically designed for Total Knee Arthroplasty (TKA) recovery management. This comprehensive platform combines AI conversation flows, clinical decision support, and real-time health monitoring to enhance patient care and reduce clinical workload.

## 🏥 System Overview

The Surgical Care Companion automates the entire patient care journey from enrollment through recovery with intelligent conversation flows, clinical risk assessment, and automated alerting.

### **Core Technologies**
- **AI Conversation Engine**: Google Gemini 2.5 Flash for contextual clinical conversations
- **Speech Processing**: OpenAI Whisper for real-time audio transcription
- **Telephony**: Twilio Voice API for automated outbound calling
- **Clinical Intelligence**: Advanced rule-based risk assessment and escalation
- **Database**: PostgreSQL with streamlined 3-table architecture
- **Backend**: FastAPI with microservices architecture
- **Containerization**: Docker Compose with multi-service orchestration
- **API Gateway**: ngrok for webhook tunneling (development)

### **Key Capabilities**
- ✅ **Intelligent Patient Enrollment** with automated call scheduling
- ✅ **Contextual AI Conversations** based on surgery timeline and patient status
- ✅ **Real-time Clinical Risk Assessment** with automatic escalation
- ✅ **Multi-channel Notifications** (Email, SMS, In-app, Webhooks)
- ✅ **Structured Conversation Flows** for comprehensive data collection
- ✅ **HIPAA-compliant Data Handling** with audit logging
- ✅ **Advanced Speech-to-Text** with streaming and batch processing
- ✅ **Clinical Decision Support** with evidence-based protocols
- ✅ **RESTful API** with comprehensive endpoint coverage
- ✅ **Database Migrations** with Alembic for schema versioning

## 🏗️ System Architecture & Service Orchestration

### **Microservices Architecture**

```mermaid
graph TB
    subgraph "External Services"
        T[Twilio Voice API]
        G[Google Gemini AI]
        W[OpenAI Whisper]
        N[ngrok Tunnel]
    end
    
    subgraph "Core Application"
        API[FastAPI Backend]
        DB[(PostgreSQL Database)]
        R[(Redis Cache)]
        
        subgraph "Services Layer"
            CS[Call Service]
            TS[Twilio Service]
            PS[Patient Service]
            NS[Notification Service]
            SS[Speech-to-Text Service]
            CM[Conversation Manager]
            CRS[Clinical Rules Service]
        end
        
        subgraph "API Layer"
            PA[Patients API]
            CA[Calls API]
            CLA[Clinical API]
            VCA[Voice Chat API]
            WH[Webhook Handlers]
        end
    end
    
    subgraph "Data Layer"
        P[Patients Table]
        CS_T[Call Sessions Table]
        CL_T[Clinical Staff Table]
        CA_T[Clinical Alerts Table]
        N_T[Notifications Table]
    end
    
    T --> API
    G --> CM
    W --> SS
    N --> WH
    
    API --> CS
    API --> PS
    API --> NS
    
    CS --> TS
    CS --> CM
    CS --> CRS
    
    PA --> PS
    CA --> CS
    CLA --> CRS
    VCA --> CM
    WH --> CS
    
    PS --> P
    CS --> CS_T
    CRS --> CL_T
    NS --> N_T
    
    DB --> P
    DB --> CS_T
    DB --> CL_T
    DB --> CA_T
    DB --> N_T
```

### **Service Communication Flow**

1. **Call Initiation**: API → Call Service → Twilio Service → Twilio API
2. **Conversation Management**: Twilio Webhook → Conversation Manager → Gemini AI
3. **Speech Processing**: Audio Input → Speech-to-Text Service → Whisper API
4. **Clinical Assessment**: Patient Response → Clinical Rules Service → Risk Evaluation
5. **Notification Dispatch**: Alert Trigger → Notification Service → Multi-channel Delivery

### **5-Phase Patient Care Workflow**

```mermaid
graph LR
    A[Patient Enrollment] --> B[Scheduled Calls]
    B --> C[AI Conversations]
    C --> D[Clinical Assessment]
    D --> E[Automated Alerts]
    E --> F[Care Team Response]
```

#### **Phase 1: Patient Enrollment** 
- Clinical staff enrolls patients 42 days before surgery
- System automatically generates complete call schedule based on surgery date
- Patient context and care plan established with baseline assessments

#### **Phase 2: Scheduled Call Execution**
- Automated outbound calls via Twilio at predetermined intervals
- Contextual conversation flows based on surgery timeline and patient status
- Real-time audio processing and transcription with error handling

#### **Phase 3: Live AI Conversations**
- Structured conversations using conversation manager
- Context-aware questions based on call type and patient status
- Real-time speech-to-text with streaming capabilities

#### **Phase 4: Clinical Risk Assessment**
- Immediate analysis of patient responses
- Clinical rules engine evaluates risk factors
- Automated escalation for concerning findings

#### **Phase 5: Care Team Notifications**
- Multi-channel alert delivery (Email, SMS, In-app)
- Priority-based routing to appropriate staff
- Complete conversation summaries for clinical review

## 📋 Comprehensive Feature Set

### **Patient Management System**
- **Smart Enrollment**: Automated call scheduling based on surgery date
- **Context-Aware Conversations**: Dynamic flows adapting to patient responses
- **Risk Stratification**: Real-time assessment with immediate escalation
- **Compliance Tracking**: Patient readiness scores and engagement metrics
- **Care Team Coordination**: Automated handoffs and notifications

### **Intelligent Conversation Engine**
- **Contextual AI Responses**: Conversations adapt to call type, timeline, and patient history
- **Structured Data Collection**: Systematic gathering of clinical information
- **Real-time Risk Detection**: Immediate identification of concerning responses
- **Multi-language Support**: Extensible for international deployments
- **Conversation State Management**: Sophisticated flow control and progress tracking

### **Advanced Audio Processing**
- **Real-time Transcription**: Streaming audio processing with OpenAI Whisper
- **Batch Audio Processing**: File upload and URL-based transcription
- **Multiple Format Support**: WAV, MP3, M4A, FLAC compatibility
- **Quality Assurance**: Confidence scoring and error handling
- **Fallback Mechanisms**: Graceful degradation when services unavailable

### **Clinical Decision Support**
- **Evidence-based Protocols**: TKA-specific clinical rules and thresholds
- **Multi-dimensional Risk Assessment**: Pain, mobility, infection, psychological factors
- **Automatic Escalation**: Priority-based routing of concerning findings
- **Clinical Analytics**: Trend analysis and outcome tracking
- **Integration Ready**: Extensible for additional surgical procedures

### **Notification & Alert System**
- **Multi-channel Delivery**: Email, SMS, in-app, and webhook notifications
- **Severity-based Routing**: Escalation paths based on clinical urgency
- **Care Team Management**: Role-based notification preferences
- **Alert History**: Complete audit trail of all notifications
- **Response Tracking**: Confirmation and follow-up capabilities

## 📅 Pre-Surgery Call Timeline

The system automatically schedules calls based on the patient's surgery date:

### **Enrollment Call (-42 days)**
- **Purpose**: Comprehensive baseline assessment
- **Duration**: ~20 minutes
- **Focus**: Surgery confirmation, mobility assessment, home safety, support system
- **Sections**: 
  - Welcome & Surgery Confirmation
  - Baseline Mobility Assessment  
  - Home Environment Safety Evaluation
  - Support System Mapping
  - Medical Optimization Review
  - Transportation Planning

### **Education Calls (Weeks 4, 3, 2, 1 before surgery)**

#### **4 Weeks Before (-28 days)**
- **Focus**: Surgery overview and recovery expectations
- **Content**: Procedure details, recovery timeline, anxiety management

#### **3 Weeks Before (-21 days)**  
- **Focus**: Home preparation requirements
- **Content**: Safety modifications, equipment needs, accessibility planning

#### **2 Weeks Before (-14 days)**
- **Focus**: Pain management planning
- **Content**: Medication strategies, non-drug approaches, expectation setting

#### **1 Week Before (-7 days)**
- **Focus**: Hospital stay preparation
- **Content**: Admission process, surgery day timeline, discharge planning

### **Final Preparation (-1 day)**
- **Purpose**: Last-minute readiness verification
- **Focus**: Final questions, anxiety management, logistics confirmation

## 🔧 Technical Implementation

## 📊 Database Schema & Data Architecture

### **Complete Database Schema**

```sql
-- =====================================================
-- CLINICAL STAFF TABLE
-- =====================================================
CREATE TABLE clinical_staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('surgeon', 'nurse', 'coordinator', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PATIENTS TABLE
-- =====================================================
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    primary_phone_number VARCHAR(20) NOT NULL,
    secondary_phone_number VARCHAR(20),
    emergency_contact VARCHAR(255),
    surgery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    primary_physician_id UUID NOT NULL REFERENCES clinical_staff(id),
    surgery_readiness_status VARCHAR(30) NOT NULL DEFAULT 'scheduled' 
        CHECK (surgery_readiness_status IN ('scheduled', 'pending', 'ready', 'done')),
    overall_compliance_score FLOAT DEFAULT 0.0 CHECK (overall_compliance_score >= 0 AND overall_compliance_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- CALL SESSIONS TABLE
-- =====================================================
CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Surgery Context
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('preop', 'postop')),
    surgery_type VARCHAR(50) NOT NULL DEFAULT 'knee',
    
    -- Call Scheduling
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    days_from_surgery INTEGER NOT NULL,  -- -42, -28, -21, -14, -7, -1, +1, +3, +7, +14, +30
    call_type VARCHAR(50) NOT NULL CHECK (call_type IN ('enrollment', 'education', 'preparation', 'final_prep', 'recovery')),
    
    -- Call Execution Status
    call_status VARCHAR(30) NOT NULL DEFAULT 'scheduled' 
        CHECK (call_status IN ('scheduled', 'in_progress', 'completed', 'failed', 'no_answer', 'cancelled')),
    actual_call_start TIMESTAMP WITH TIME ZONE,
    call_duration_seconds INTEGER CHECK (call_duration_seconds >= 0),
    call_outcome VARCHAR(50) CHECK (call_outcome IN ('successful', 'no_answer', 'busy', 'failed', 'voicemail')),
    
    -- AI Analysis Results
    agent_notes TEXT,
    compliance_score INTEGER CHECK (compliance_score >= 0 AND compliance_score <= 100),
    concerns_identified TEXT[],  -- Array of concern categories
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Audio & Transcription
    audio_file_path VARCHAR(500),
    transcript TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- CLINICAL ALERTS TABLE
-- =====================================================
CREATE TABLE clinical_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    call_session_id UUID REFERENCES call_sessions(id) ON DELETE SET NULL,
    assigned_staff_id UUID REFERENCES clinical_staff(id),
    
    -- Alert Details
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('pain', 'mobility', 'infection', 'medication', 'psychological', 'other')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    
    -- Alert Status
    status VARCHAR(30) NOT NULL DEFAULT 'open' 
        CHECK (status IN ('open', 'acknowledged', 'in_progress', 'resolved', 'dismissed')),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID REFERENCES clinical_staff(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES clinical_staff(id),
    resolution_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- NOTIFICATIONS TABLE
-- =====================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    clinical_alert_id UUID REFERENCES clinical_alerts(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES clinical_staff(id),
    
    -- Notification Details
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('email', 'sms', 'push', 'webhook')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Delivery Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Priority & Routing
    priority VARCHAR(20) NOT NULL DEFAULT 'normal' 
        CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX idx_patients_surgery_date ON patients(surgery_date);
CREATE INDEX idx_patients_physician ON patients(primary_physician_id);
CREATE INDEX idx_call_sessions_patient ON call_sessions(patient_id);
CREATE INDEX idx_call_sessions_scheduled ON call_sessions(scheduled_date);
CREATE INDEX idx_call_sessions_status ON call_sessions(call_status);
CREATE INDEX idx_clinical_alerts_patient ON clinical_alerts(patient_id);
CREATE INDEX idx_clinical_alerts_status ON clinical_alerts(status);
CREATE INDEX idx_clinical_alerts_severity ON clinical_alerts(severity);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_status ON notifications(status);

-- =====================================================
-- SAMPLE DATA FUNCTIONS
-- =====================================================
-- Function to auto-schedule calls when patient is enrolled
CREATE OR REPLACE FUNCTION schedule_patient_calls()
RETURNS TRIGGER AS $$
DECLARE
    call_dates INTEGER[] := ARRAY[-42, -28, -21, -14, -7, -1];
    call_types VARCHAR[] := ARRAY['enrollment', 'education', 'education', 'education', 'preparation', 'final_prep'];
    i INTEGER;
BEGIN
    FOR i IN 1..array_length(call_dates, 1) LOOP
        INSERT INTO call_sessions (
            patient_id, 
            stage, 
            surgery_type, 
            scheduled_date, 
            days_from_surgery, 
            call_type
        ) VALUES (
            NEW.id,
            'preop',
            'knee',
            NEW.surgery_date + (call_dates[i] || ' days')::INTERVAL,
            call_dates[i],
            call_types[i]
        );
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-schedule calls
CREATE TRIGGER trigger_schedule_calls
    AFTER INSERT ON patients
    FOR EACH ROW
    EXECUTE FUNCTION schedule_patient_calls();
```

### **Data Flow & Relationships**

```mermaid
erDiagram
    CLINICAL_STAFF ||--o{ PATIENTS : "primary_physician"
    CLINICAL_STAFF ||--o{ CLINICAL_ALERTS : "assigned_to"
    CLINICAL_STAFF ||--o{ NOTIFICATIONS : "receives"
    
    PATIENTS ||--o{ CALL_SESSIONS : "has_calls"
    PATIENTS ||--o{ CLINICAL_ALERTS : "generates_alerts"
    PATIENTS ||--o{ NOTIFICATIONS : "triggers_notifications"
    
    CALL_SESSIONS ||--o{ CLINICAL_ALERTS : "may_create_alert"
    
    CLINICAL_ALERTS ||--o{ NOTIFICATIONS : "sends_notifications"
    
    CLINICAL_STAFF {
        uuid id PK
        string name
        string email
        string role
        timestamp created_at
    }
    
    PATIENTS {
        uuid id PK
        string name
        string primary_phone
        string secondary_phone
        string emergency_contact
        timestamp surgery_date
        uuid primary_physician_id FK
        string readiness_status
        float compliance_score
        timestamp created_at
    }
    
    CALL_SESSIONS {
        uuid id PK
        uuid patient_id FK
        string stage
        string surgery_type
        timestamp scheduled_date
        int days_from_surgery
        string call_type
        string call_status
        timestamp actual_call_start
        int call_duration_seconds
        string call_outcome
        text agent_notes
        int compliance_score
        text_array concerns_identified
        string risk_level
        text transcript
        timestamp created_at
    }
    
    CLINICAL_ALERTS {
        uuid id PK
        uuid patient_id FK
        uuid call_session_id FK
        uuid assigned_staff_id FK
        string alert_type
        string severity
        string title
        text description
        string status
        timestamp acknowledged_at
        uuid acknowledged_by FK
        timestamp resolved_at
        uuid resolved_by FK
        text resolution_notes
        timestamp created_at
    }
    
    NOTIFICATIONS {
        uuid id PK
        uuid patient_id FK
        uuid clinical_alert_id FK
        uuid recipient_id FK
        string notification_type
        string title
        text message
        string status
        timestamp sent_at
        timestamp delivered_at
        string priority
        timestamp created_at
    }
```
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients with Surgery Timeline
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    primary_phone_number VARCHAR(20) NOT NULL,
    secondary_phone_number VARCHAR(20),
    surgery_date TIMESTAMP NOT NULL,
    primary_physician_id UUID REFERENCES clinical_staff(id),
    surgery_readiness_status VARCHAR(30) DEFAULT 'pending',
    overall_compliance_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Call Sessions with AI Analysis
CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    stage VARCHAR(50) NOT NULL,  -- preop/postop
    surgery_type VARCHAR(50) NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    days_from_surgery INTEGER NOT NULL,  -- -42, -28, -21, -14, -7, -1
    call_type VARCHAR(50) NOT NULL,  -- enrollment, education, preparation
    call_status VARCHAR(30) DEFAULT 'scheduled',
    agent_notes TEXT,  -- AI-generated structured summaries
    compliance_score INTEGER,  -- 0-100 call assessment
    concerns_identified TEXT[],  -- Array of flagged issues
    actual_call_start TIMESTAMP,
    actual_call_end TIMESTAMP,
    call_sid VARCHAR(100),  -- Twilio call identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Service Architecture**

#### **Core Services**
- **`CallContextService`**: Manages call-specific context and conversation structures
- **`ConversationManager`**: Orchestrates conversation flows and state management
- **`ClinicalRulesService`**: Implements evidence-based risk assessment protocols
- **`SpeechToTextService`**: Handles audio transcription with streaming support
- **`VoiceChatService`**: Generates contextual AI responses using Gemini
- **`NotificationService`**: Multi-channel alert delivery and management
- **`CallOrchestrationService`**: Coordinates Twilio integration and call lifecycle

#### **API Endpoints**

##### **Patient Management**
```
POST /api/v1/patients/enroll          # Enroll new patient with auto-scheduling
GET  /api/v1/patients/{id}/calls      # Get patient's call schedule
GET  /api/v1/patients/staff/list      # List available clinical staff
```

##### **Conversation Management**
```
POST /api/v1/voice-chat/start-conversation-flow  # Begin structured conversation
POST /api/v1/voice-chat/conversation-flow        # Process conversation messages
GET  /api/v1/voice-chat/conversation-status/{id} # Check conversation progress
POST /api/v1/voice-chat/end-conversation/{id}    # Complete conversation
```

##### **Call Operations**
```
POST /api/v1/calls/initiate           # Start outbound call to patient
GET  /api/v1/calls/status/{id}        # Get detailed call status
GET  /api/v1/calls/transcripts/{id}   # Retrieve conversation transcripts
POST /api/v1/calls/complete/{id}      # Mark call as completed
```

##### **Clinical Support**
```
GET  /api/v1/clinical/alerts          # View active clinical alerts
POST /api/v1/clinical/alerts/resolve  # Mark alerts as resolved
GET  /api/v1/clinical/analytics       # Clinical performance metrics
```

## 🚀 Quick Start Guide

### **Prerequisites**
- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (for caching and sessions)
- Docker & Docker Compose
- Twilio Account (for voice calls)
- Google AI Studio Account (for Gemini API)

### **Environment Setup**

1. **Clone Repository**
```bash
git clone https://github.com/your-repo/surgical-care-companion.git
cd surgical-care-companion
```

2. **Configure Environment**
```bash
cp .env.example .env
```

**Required Environment Variables:**
```env
# Core Database
DATABASE_URL=postgresql://user:password@localhost:5432/surgical_care

# AI Services
GEMINI_API_KEY=your-gemini-api-key-here
WHISPER_MODEL=base  # or small, medium, large

# Twilio Integration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-ngrok-url.com

# Notification Services
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security
SECRET_KEY=your-secret-key-here
```

3. **Start Services**
```bash
# Using Docker Compose (Recommended)
docker-compose up --build

# Or manually
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

4. **Initialize Database**
```bash
# Run database migrations
python backend/scripts/run_migrations.py

# Create sample data
python backend/scripts/init_db.py

# Set up test patient with education calls
python backend/scripts/setup_education_test.py
```

### **Twilio Webhook Configuration**

1. **Start ngrok for local development:**
```bash
# ngrok is included in docker-compose for convenience
docker-compose up ngrok_voice_agent

# Or manually:
ngrok http 8000
```

2. **Configure Twilio Webhooks:**
- Voice Webhook URL: `https://your-ngrok-url.com/api/v1/twilio/voice-webhook/{call_session_id}`
- SMS Webhook URL: `https://your-ngrok-url.com/api/v1/twilio/sms-webhook`

### **Verify Installation**

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/patients/staff/list

# Check Twilio integration
curl http://localhost:8000/api/v1/calls/twilio-status
```

## 📊 Usage Examples

### **1. Enroll a New Patient**
```bash
curl -X POST "http://localhost:8000/api/v1/patients/enroll" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "primary_phone_number": "+1234567890",
    "surgery_date": "2024-02-15T10:00:00Z",
    "primary_physician_id": "physician-uuid-here",
    "surgery_type": "knee"
  }'
```

### **2. Start a Conversation Flow**
```bash
curl -X POST "http://localhost:8000/api/v1/voice-chat/start-conversation-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid",
    "call_session_id": "session-uuid"
  }'
```

### **3. Initiate Outbound Call**
```bash
curl -X POST "http://localhost:8000/api/v1/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid",
    "call_session_id": "session-uuid",
    "call_type": "education",
    "priority": "normal"
  }'
```

## 🔒 Security & Compliance

### **HIPAA Compliance Features**
- **Data Encryption**: All PHI encrypted at rest and in transit
- **Access Controls**: Role-based permissions for clinical staff
- **Audit Logging**: Complete trail of all patient interactions
- **Secure Communications**: TLS encryption for all API endpoints
- **Data Minimization**: Only necessary clinical data collected
- **Patient Consent**: Built-in consent management workflows

### **Security Best Practices**
- **API Authentication**: JWT-based session management
- **Input Validation**: Comprehensive sanitization of all inputs
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Webhook Validation**: Twilio request signature verification
- **Environment Isolation**: Separate development/staging/production environments

## 🧪 Comprehensive Testing Guide

### **Environment Setup for Testing**

```bash
# 1. Clone and setup the repository
git clone <repository-url>
cd surgical-care-companion

# 2. Copy environment configuration
cp .env.example .env

# 3. Update .env with your credentials:
# - Twilio Account SID, Auth Token, Phone Number
# - Google Gemini API Key
# - OpenAI API Key (for Whisper)
# - Database credentials
# - ngrok Auth Token

# 4. Start all services
docker-compose up -d

# 5. Run database migrations
docker-compose exec backend python scripts/run_migrations.py

# 6. Initialize test data
docker-compose exec backend python scripts/setup_education_test.py
```

### **Testing Commands & Workflows**

#### **1. Unit Testing**
```bash
# Run all unit tests
docker-compose exec backend python -m pytest tests/test_unit.py -v

# Run specific test categories
docker-compose exec backend python -m pytest tests/test_unit.py::test_patient_service -v
docker-compose exec backend python -m pytest tests/test_unit.py::test_call_service -v
docker-compose exec backend python -m pytest tests/test_unit.py::test_twilio_service -v

# Run with coverage
docker-compose exec backend python -m pytest tests/test_unit.py --cov=. --cov-report=html
```

#### **2. Integration Testing**
```bash
# Full integration test suite
docker-compose exec backend python -m pytest tests/test_integration.py -v

# Test specific integrations
docker-compose exec backend python -m pytest tests/test_integration.py::test_patient_enrollment_flow -v
docker-compose exec backend python -m pytest tests/test_integration.py::test_call_initiation_flow -v
docker-compose exec backend python -m pytest tests/test_integration.py::test_webhook_processing -v

# Test external service integrations
docker-compose exec backend python -m pytest tests/test_integration.py::test_twilio_integration -v
docker-compose exec backend python -m pytest tests/test_integration.py::test_gemini_integration -v
```

#### **3. API Testing with curl Commands**

##### **Patient Management**
```bash
# Create a new patient
curl -X POST "http://localhost:8000/api/patients/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "primary_phone_number": "+12132757114",
    "secondary_phone_number": "+12132757115",
    "emergency_contact": "John Doe - Husband - +12132757116",
    "surgery_date": "2025-08-15T09:00:00Z",
    "primary_physician_id": "physician-uuid-here"
  }'

# Get all patients
curl -X GET "http://localhost:8000/api/patients/"

# Get specific patient
curl -X GET "http://localhost:8000/api/patients/{patient_id}"

# Update patient
curl -X PUT "http://localhost:8000/api/patients/{patient_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "emergency_contact": "Updated contact info"
  }'
```

##### **Call Management**
```bash
# Initiate a call to patient
curl -X POST "http://localhost:8000/api/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid-here",
    "call_type": "education"
  }'

# Get call history for patient
curl -X GET "http://localhost:8000/api/calls/patient/{patient_id}/history"

# Get specific call session details
curl -X GET "http://localhost:8000/api/calls/{call_session_id}"

# Update call session with results
curl -X PUT "http://localhost:8000/api/calls/{call_session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "call_status": "completed",
    "call_outcome": "successful",
    "agent_notes": "Patient doing well, no concerns",
    "compliance_score": 85,
    "concerns_identified": []
  }'
```

##### **Clinical Staff Management**
```bash
# Create clinical staff member
curl -X POST "http://localhost:8000/api/clinical/staff" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Smith",
    "email": "dr.smith@hospital.com",
    "role": "surgeon"
  }'

# Get all clinical staff
curl -X GET "http://localhost:8000/api/clinical/staff"

# Get clinical alerts
curl -X GET "http://localhost:8000/api/clinical/alerts"

# Create clinical alert
curl -X POST "http://localhost:8000/api/clinical/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-uuid-here",
    "alert_type": "pain",
    "severity": "high",
    "title": "High Pain Level Reported",
    "description": "Patient reported pain level 8/10 during call"
  }'
```

##### **Speech-to-Text Testing**
```bash
# Test speech-to-text with file upload
curl -X POST "http://localhost:8000/api/voice-chat/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@test_audio.wav"

# Test speech-to-text with URL
curl -X POST "http://localhost:8000/api/voice-chat/transcribe-url" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/audio.wav"
  }'

# Test streaming transcription
curl -X POST "http://localhost:8000/api/voice-chat/transcribe-stream" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_chunk=@audio_chunk.wav"
```

#### **4. Database Testing**
```bash
# View database contents
docker-compose exec backend python scripts/view_database.py

# Test database connectivity
docker-compose exec postgres psql -U user -d tka_voice -c "SELECT COUNT(*) FROM patients;"

# Run database migrations
docker-compose exec backend python scripts/run_migrations.py

# Reset database with test data
docker-compose exec backend python scripts/init_db.py
```

#### **5. Webhook Testing with ngrok**
```bash
# Start ngrok tunnel (in separate terminal)
ngrok http 8000 --authtoken YOUR_NGROK_TOKEN

# Update TWILIO_WEBHOOK_URL in .env with ngrok URL
# Restart backend
docker-compose restart backend

# Test webhook endpoint directly
curl -X POST "https://your-ngrok-url.ngrok-free.app/webhooks/twilio/voice" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test123&From=%2B12132757114&To=%2B18776589089&CallStatus=in-progress"
```

### **End-to-End Testing Workflow**

#### **Complete Patient Journey Test**
```bash
#!/bin/bash
# test_complete_workflow.sh

echo "🏥 Starting Complete Patient Care Workflow Test"

# 1. Create clinical staff
STAFF_ID=$(curl -s -X POST "http://localhost:8000/api/clinical/staff" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Test Surgeon",
    "email": "test@hospital.com",
    "role": "surgeon"
  }' | jq -r '.id')

echo "✅ Created staff member: $STAFF_ID"

# 2. Create patient (auto-schedules calls)
PATIENT_ID=$(curl -s -X POST "http://localhost:8000/api/patients/" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Patient\",
    \"primary_phone_number\": \"+12132757114\",
    \"surgery_date\": \"$(date -d '+42 days' --iso-8601)T09:00:00Z\",
    \"primary_physician_id\": \"$STAFF_ID\",
    \"surgery_type\": \"knee\"
  }" | jq -r '.id')

echo "✅ Created patient: $PATIENT_ID"

# 3. Verify call schedule was created
CALL_COUNT=$(curl -s "http://localhost:8000/api/calls/patient/$PATIENT_ID/history" | jq '. | length')
echo "✅ Auto-scheduled $CALL_COUNT calls"

# 4. Initiate enrollment call
CALL_ID=$(curl -s -X POST "http://localhost:8000/api/calls/initiate" \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"$PATIENT_ID\",
    \"call_type\": \"enrollment\"
  }" | jq -r '.call_session_id')

echo "✅ Initiated enrollment call: $CALL_ID"

# 5. Check call status
sleep 5
CALL_STATUS=$(curl -s "http://localhost:8000/api/calls/$CALL_ID" | jq -r '.call_status')
echo "✅ Call status: $CALL_STATUS"

echo "🎉 Complete workflow test finished!"
```

### **Performance Testing**
```bash
# Load testing with Apache Bench
# Test patient creation endpoint
ab -n 100 -c 10 -p patient_data.json -T application/json \
  http://localhost:8000/api/patients/

# Test call initiation endpoint
ab -n 50 -c 5 -p call_data.json -T application/json \
  http://localhost:8000/api/calls/initiate

# Monitor system resources during testing
docker stats
```

### **Service Health Checks**
```bash
# Check all service health
curl http://localhost:8000/health
curl http://localhost:8000/api/health

# Check specific service components
curl http://localhost:8000/api/health/database
curl http://localhost:8000/api/health/redis
curl http://localhost:8000/api/health/twilio
curl http://localhost:8000/api/health/gemini

# Check system metrics
curl http://localhost:8000/api/metrics
```

## 🚀 Production Deployment Guide

### **Docker Production Setup**
```bash
# 1. Build production images
docker-compose -f docker-compose.prod.yml build

# 2. Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# 3. Run production migrations
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/run_migrations.py

# 4. Set up SSL with Let's Encrypt
certbot --nginx -d your-domain.com

# 5. Configure production secrets
echo "TWILIO_AUTH_TOKEN=prod_token" >> .env.prod
echo "DATABASE_URL=postgresql://prod_user:prod_pass@prod_db:5432/tka_voice" >> .env.prod
```

### **Monitoring & Logging**
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# Export logs for analysis
docker-compose logs backend > backend.log
docker-compose logs postgres > postgres.log

# Monitor resource usage
docker system df
docker system prune  # cleanup unused resources
```

## 📱 API Reference

### **Core Endpoints Overview**

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/api/patients/` | GET, POST | Patient management | Required |
| `/api/patients/{id}` | GET, PUT, DELETE | Individual patient ops | Required |
| `/api/calls/initiate` | POST | Start patient call | Required |
| `/api/calls/{id}` | GET, PUT | Call session details | Required |
| `/api/clinical/staff` | GET, POST | Staff management | Required |
| `/api/clinical/alerts` | GET, POST | Alert management | Required |
| `/api/voice-chat/transcribe` | POST | Audio transcription | Required |
| `/webhooks/twilio/voice` | POST | Twilio voice webhook | Public |
| `/health` | GET | System health check | Public |

### **Response Formats**

#### **Success Response**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "created_at": "2025-07-14T10:00:00Z"
  },
  "message": "Operation completed successfully"
}
```

#### **Error Response**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "primary_phone_number",
      "expected_format": "+1XXXXXXXXXX"
    }
  }
}
```

## 🔧 Configuration Management

### **Environment Variables Reference**

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=           # Your Twilio Account SID
TWILIO_AUTH_TOKEN=            # Your Twilio Auth Token  
TWILIO_PHONE_NUMBER=          # Your Twilio phone number (+1XXXXXXXXXX)
TWILIO_WEBHOOK_URL=           # Public URL for webhooks (ngrok in dev)

# AI Services
GEMINI_API_KEY=               # Google Gemini API key
GEMINI_MODEL=                 # Model version (gemini-2.5-flash)
OPENAI_API_KEY=               # OpenAI API key for Whisper
WHISPER_MODEL=                # Whisper model size (base/small/medium/large)

# Database
DATABASE_URL=                 # PostgreSQL connection string
DB_HOST=                      # Database host
DB_PORT=                      # Database port (5432)
DB_USER=                      # Database username
DB_PASSWORD=                  # Database password
DB_NAME=                      # Database name

# Redis
REDIS_URL=                    # Redis connection string
REDIS_HOST=                   # Redis host
REDIS_PORT=                   # Redis port (6379)

# Application
ENVIRONMENT=                  # Environment (development/staging/production)
DEBUG=                        # Debug mode (true/false)
LOG_LEVEL=                    # Logging level (DEBUG/INFO/WARNING/ERROR)
HOST=                         # Application host (0.0.0.0)
PORT=                         # Application port (8000)

# Security
SECRET_KEY=                   # JWT secret key (32+ characters)
ALGORITHM=                    # JWT algorithm (HS256)
ACCESS_TOKEN_EXPIRE_MINUTES=  # Token expiration (30)

# Clinical Settings
DEFAULT_CALL_SCHEDULE=        # Days from surgery for calls [-42,-28,-21,-14,-7,-1]
MAX_CALL_DURATION_MINUTES=    # Maximum call duration (15)
URGENT_ALERT_THRESHOLD=       # Pain score threshold for urgent alerts (7)
```

### **Docker Compose Services**

```yaml
services:
  backend:          # FastAPI application server
  postgres:         # PostgreSQL database
  redis:           # Redis cache and session store
  ngrok:           # Reverse proxy for webhook tunneling (dev only)
```

## 🐛 Troubleshooting Guide

### **Common Issues & Solutions**

#### **Database Connection Issues**
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python scripts/init_db.py
```

#### **Twilio Webhook Issues**
```bash
# Verify ngrok tunnel
curl https://your-ngrok-url.ngrok-free.app/health

# Check webhook URL in Twilio console
# Update TWILIO_WEBHOOK_URL in .env
# Restart backend service
docker-compose restart backend
```

#### **Call Initiation Failures**
```bash
# Verify Twilio credentials
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}.json" \
  -u $TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN

# Check phone number format
# Must be E.164 format: +1XXXXXXXXXX

# Verify patient exists in database
curl http://localhost:8000/api/patients/{patient_id}
```

#### **Audio Processing Issues**
```bash
# Check OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Verify audio file format
file audio_sample.wav  # Should show: RIFF (little-endian) data, WAVE audio

# Test speech-to-text service independently
curl -X POST http://localhost:8001/transcribe \
  -F "audio_file=@test_audio.wav"
```

### **Log Analysis**

```bash
# Backend application logs
docker-compose logs backend | grep "ERROR\|WARN"

# Database query logs
docker-compose logs postgres | grep "STATEMENT"

# Twilio webhook logs
docker-compose logs backend | grep "webhook"

# AI service logs
docker-compose logs backend | grep "gemini\|whisper"
```

---

## 🎯 Future Roadmap

### **Planned Features**
- **Multi-Provider Support**: Support for multiple healthcare organizations
- **Advanced Analytics**: Machine learning-based outcome prediction
- **Patient Portal**: Self-service portal for patients to view their progress
- **Mobile App**: Native iOS/Android applications for care teams
- **Advanced Integrations**: Epic, Cerner, and other major EHR systems
- **Telehealth Integration**: Video call capabilities for complex cases

### **Research Initiatives**
- **Outcome Studies**: Clinical effectiveness research partnerships
- **AI Improvements**: Enhanced natural language understanding
- **Predictive Analytics**: Early identification of complications
- **Population Health**: Aggregate analytics for quality improvement

---

*Built with ❤️ for better patient care and clinical efficiency. This system represents the future of post-surgical monitoring - intelligent, scalable, and deeply integrated with clinical workflows.*