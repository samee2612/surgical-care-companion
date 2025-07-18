-- Unified Database Schema for Surgical Care Companion
-- Compatible with both Frontend (TypeScript/Drizzle) and Backend (Python/SQLAlchemy)

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE (For authentication and staff management)
-- ============================================================================

CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    profile_image_url VARCHAR(500),
    role VARCHAR(50) NOT NULL DEFAULT 'provider', -- provider, admin, patient
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SESSIONS TABLE (For Replit Auth)
-- ============================================================================

CREATE TABLE sessions (
    sid VARCHAR(255) PRIMARY KEY,
    sess JSONB NOT NULL,
    expire TIMESTAMP NOT NULL
);

CREATE INDEX idx_session_expire ON sessions(expire);

-- ============================================================================
-- PATIENTS TABLE (Unified structure)
-- ============================================================================

CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    mrn VARCHAR(255) UNIQUE, -- Medical Record Number
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    phone VARCHAR(20),
    email VARCHAR(255),
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    voice_consent_given BOOLEAN DEFAULT FALSE,
    data_consent_given BOOLEAN DEFAULT FALSE,
    program_active BOOLEAN DEFAULT TRUE,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for patients
CREATE INDEX idx_patients_phone ON patients(phone);
CREATE INDEX idx_patients_mrn ON patients(mrn);
CREATE INDEX idx_patients_email ON patients(email);

-- ============================================================================
-- SURGERIES TABLE 
-- ============================================================================

CREATE TABLE surgeries (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    procedure VARCHAR(255) NOT NULL,
    surgeon_name VARCHAR(255) NOT NULL,
    surgery_date DATE NOT NULL,
    discharge_date DATE,
    expected_recovery_weeks INTEGER,
    specialty VARCHAR(100) NOT NULL, -- orthopedic, cardiac, general, neuro
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for surgeries
CREATE INDEX idx_surgeries_patient_id ON surgeries(patient_id);
CREATE INDEX idx_surgeries_surgery_date ON surgeries(surgery_date);

-- ============================================================================
-- VOICE INTERACTIONS TABLE (For call logs and conversations)
-- ============================================================================

CREATE TABLE voice_interactions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    surgery_id INTEGER NOT NULL REFERENCES surgeries(id),
    call_date TIMESTAMP NOT NULL,
    call_duration INTEGER, -- in seconds
    call_sid VARCHAR(255) UNIQUE, -- Twilio Call SID
    phone_number VARCHAR(20),
    call_direction VARCHAR(20), -- inbound, outbound
    call_status VARCHAR(50), -- completed, failed, busy, etc.
    transcript TEXT,
    audio_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for voice interactions
CREATE INDEX idx_voice_interactions_patient_id ON voice_interactions(patient_id);
CREATE INDEX idx_voice_interactions_surgery_id ON voice_interactions(surgery_id);
CREATE INDEX idx_voice_interactions_call_date ON voice_interactions(call_date);
CREATE INDEX idx_voice_interactions_call_sid ON voice_interactions(call_sid);

-- ============================================================================
-- CONVERSATION MESSAGES TABLE (For detailed conversation tracking)
-- ============================================================================

CREATE TABLE conversation_messages (
    id SERIAL PRIMARY KEY,
    voice_interaction_id INTEGER NOT NULL REFERENCES voice_interactions(id),
    role VARCHAR(50) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    timestamp_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence DECIMAL(3,2), -- 0.00 to 1.00
    audio_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for conversation messages
CREATE INDEX idx_conversation_messages_interaction_id ON conversation_messages(voice_interaction_id);
CREATE INDEX idx_conversation_messages_timestamp ON conversation_messages(timestamp_utc);

-- ============================================================================
-- ASSESSMENTS TABLE (For clinical assessments from AI analysis)
-- ============================================================================

CREATE TABLE assessments (
    id SERIAL PRIMARY KEY,
    voice_interaction_id INTEGER NOT NULL REFERENCES voice_interactions(id),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    assessment_type VARCHAR(100) NOT NULL, -- pain, wound, medication, general
    assessment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Clinical Data
    pain_level INTEGER CHECK (pain_level >= 0 AND pain_level <= 10),
    symptoms JSONB, -- Array of symptoms
    concerns JSONB, -- Array of concerns
    medications JSONB, -- Medication status
    
    -- AI Analysis Results
    sentiment VARCHAR(50), -- positive, negative, neutral
    urgency_level VARCHAR(50), -- low, medium, high, critical
    intent VARCHAR(100), -- pain_inquiry, wound_check, medication_question, etc.
    entities JSONB, -- Extracted entities
    
    -- Clinical Recommendations
    recommended_actions JSONB, -- Array of recommended actions
    requires_immediate_attention BOOLEAN DEFAULT FALSE,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for assessments
CREATE INDEX idx_assessments_voice_interaction_id ON assessments(voice_interaction_id);
CREATE INDEX idx_assessments_patient_id ON assessments(patient_id);
CREATE INDEX idx_assessments_assessment_date ON assessments(assessment_date);
CREATE INDEX idx_assessments_urgency_level ON assessments(urgency_level);

-- ============================================================================
-- CLINICAL STAFF TABLE (For healthcare providers)
-- ============================================================================

CREATE TABLE clinical_staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL, -- surgeon, nurse, coordinator, admin
    specialty VARCHAR(100), -- orthopedic, cardiac, etc.
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for clinical staff
CREATE INDEX idx_clinical_staff_email ON clinical_staff(email);
CREATE INDEX idx_clinical_staff_role ON clinical_staff(role);

-- ============================================================================
-- PATIENT CARE ASSIGNMENTS TABLE (Link patients to care teams)
-- ============================================================================

CREATE TABLE patient_care_assignments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    clinical_staff_id UUID NOT NULL REFERENCES clinical_staff(id),
    role VARCHAR(50) NOT NULL, -- primary_surgeon, nurse, coordinator
    assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for patient care assignments
CREATE INDEX idx_patient_care_assignments_patient_id ON patient_care_assignments(patient_id);
CREATE INDEX idx_patient_care_assignments_staff_id ON patient_care_assignments(clinical_staff_id);

-- ============================================================================
-- NOTIFICATIONS TABLE (For alerts and notifications)
-- ============================================================================

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient_id UUID NOT NULL REFERENCES clinical_staff(id),
    patient_id INTEGER REFERENCES patients(id),
    voice_interaction_id INTEGER REFERENCES voice_interactions(id),
    assessment_id INTEGER REFERENCES assessments(id),
    
    notification_type VARCHAR(100) NOT NULL, -- urgent_symptom, missed_call, assessment_alert
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'medium', -- low, medium, high, critical
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES clinical_staff(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for notifications
CREATE INDEX idx_notifications_recipient_id ON notifications(recipient_id);
CREATE INDEX idx_notifications_patient_id ON notifications(patient_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_severity ON notifications(severity);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- ============================================================================
-- CALL SCHEDULES TABLE (For scheduling automated calls)
-- ============================================================================

CREATE TABLE call_schedules (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    surgery_id INTEGER NOT NULL REFERENCES surgeries(id),
    
    schedule_type VARCHAR(50) NOT NULL, -- post_op_day_1, post_op_day_3, weekly, etc.
    scheduled_date TIMESTAMP NOT NULL,
    actual_call_date TIMESTAMP,
    call_completed BOOLEAN DEFAULT FALSE,
    
    voice_interaction_id INTEGER REFERENCES voice_interactions(id),
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for call schedules
CREATE INDEX idx_call_schedules_patient_id ON call_schedules(patient_id);
CREATE INDEX idx_call_schedules_scheduled_date ON call_schedules(scheduled_date);
CREATE INDEX idx_call_schedules_completed ON call_schedules(call_completed);

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample clinical staff
INSERT INTO clinical_staff (id, name, email, role, specialty) VALUES
(gen_random_uuid(), 'Dr. Sarah Johnson', 'sarah.johnson@hospital.com', 'surgeon', 'orthopedic'),
(gen_random_uuid(), 'Nurse Mary Smith', 'mary.smith@hospital.com', 'nurse', 'post_surgical'),
(gen_random_uuid(), 'John Coordinator', 'john.coord@hospital.com', 'coordinator', 'patient_care');

-- Insert sample patients
INSERT INTO patients (mrn, first_name, last_name, date_of_birth, phone, email, voice_consent_given, data_consent_given) VALUES
('MRN001', 'John', 'Doe', '1980-01-15', '2132757114', 'john.doe@email.com', true, true),
('MRN002', 'Jane', 'Smith', '1975-05-22', '2132757115', 'jane.smith@email.com', true, true),
('MRN003', 'Bob', 'Wilson', '1965-12-10', '2132757116', 'bob.wilson@email.com', true, true);

-- Insert sample surgeries
INSERT INTO surgeries (patient_id, procedure, surgeon_name, surgery_date, specialty, expected_recovery_weeks) VALUES
(1, 'Total Knee Arthroplasty', 'Dr. Sarah Johnson', '2025-07-10', 'orthopedic', 8),
(2, 'Hip Replacement', 'Dr. Sarah Johnson', '2025-07-12', 'orthopedic', 10),
(3, 'Shoulder Arthroscopy', 'Dr. Sarah Johnson', '2025-07-08', 'orthopedic', 6);

-- Insert sample care assignments
INSERT INTO patient_care_assignments (patient_id, clinical_staff_id, role) VALUES
(1, (SELECT id FROM clinical_staff WHERE email = 'sarah.johnson@hospital.com'), 'primary_surgeon'),
(1, (SELECT id FROM clinical_staff WHERE email = 'mary.smith@hospital.com'), 'nurse'),
(2, (SELECT id FROM clinical_staff WHERE email = 'sarah.johnson@hospital.com'), 'primary_surgeon'),
(2, (SELECT id FROM clinical_staff WHERE email = 'mary.smith@hospital.com'), 'nurse'),
(3, (SELECT id FROM clinical_staff WHERE email = 'sarah.johnson@hospital.com'), 'primary_surgeon'),
(3, (SELECT id FROM clinical_staff WHERE email = 'mary.smith@hospital.com'), 'nurse');

-- Insert sample call schedules
INSERT INTO call_schedules (patient_id, surgery_id, schedule_type, scheduled_date) VALUES
(1, 1, 'post_op_day_1', '2025-07-11 10:00:00'),
(1, 1, 'post_op_day_3', '2025-07-13 10:00:00'),
(2, 2, 'post_op_day_1', '2025-07-13 10:00:00'),
(2, 2, 'post_op_day_3', '2025-07-15 10:00:00'),
(3, 3, 'post_op_day_1', '2025-07-09 10:00:00'),
(3, 3, 'post_op_day_3', '2025-07-11 10:00:00');
