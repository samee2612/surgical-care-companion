-- TKA Voice Agent - PostgreSQL Database Schema
-- Simplified database structure for post-surgical patient monitoring system

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CLINICAL STAFF TABLE
-- ============================================================================

CREATE TABLE clinical_staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'surgeon', 'nurse', 'coordinator'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PATIENTS TABLE
-- ============================================================================

CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    primary_phone VARCHAR(20) NOT NULL,
    secondary_phone VARCHAR(20),
    surgery_date TIMESTAMP NOT NULL,
    primary_physician_id UUID REFERENCES clinical_staff(id), -- Made nullable for easier enrollment
    
    -- Core readiness tracking
    surgery_readiness_status VARCHAR(30) NOT NULL DEFAULT 'done',
    report JSON NOT NULL DEFAULT '{}'::json,
    
    overall_compliance_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CALL SESSIONS TABLE
-- ============================================================================

CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    stage VARCHAR(50) NOT NULL, -- 'preop/postop'
    surgery_type VARCHAR(50) NOT NULL, -- 'hip', 'knee', 'shoulder', 'elbow', 'wrist', 'finger', 'toe', 'other'

    -- When to call
    scheduled_date TIMESTAMP NOT NULL,
    days_from_surgery INTEGER NOT NULL, -- -42, -28, -21, -14, -7, -1, +1, +3, +7
    call_type VARCHAR(50) NOT NULL, -- 'enrollment', 'education', 'preparation', 'final_prep'
    
    -- Call execution
    call_status VARCHAR(30) NOT NULL DEFAULT 'scheduled', -- Values: 'scheduled', 'completed', 'failed', 'rescheduled'
    actual_call_start TIMESTAMP,
    call_duration_seconds INTEGER,
    call_outcome VARCHAR(50), -- 'successful', 'no_answer', 'concerning'
    
    -- AI agent summary (contains everything)
    conversation_history JSON NOT NULL DEFAULT '[]'::json,
    agent_notes TEXT, -- AI writes structured summary here
    compliance_score INTEGER, -- Overall call score 0-100
    concerns_identified TEXT[], -- Array of specific concerns
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Patient indexes
CREATE INDEX idx_patients_primary_phone ON patients(primary_phone);
CREATE INDEX idx_patients_surgery_date ON patients(surgery_date);
CREATE INDEX idx_patients_physician ON patients(primary_physician_id);

-- Call session indexes
CREATE INDEX idx_call_sessions_patient ON call_sessions(patient_id);
CREATE INDEX idx_call_sessions_status ON call_sessions(call_status);
CREATE INDEX idx_call_sessions_scheduled_date ON call_sessions(scheduled_date);
CREATE INDEX idx_call_sessions_days_from_surgery ON call_sessions(days_from_surgery);
CREATE INDEX idx_call_sessions_surgery_type ON call_sessions(surgery_type);

-- Clinical staff indexes
CREATE INDEX idx_clinical_staff_role ON clinical_staff(role);
CREATE INDEX idx_clinical_staff_email ON clinical_staff(email);

-- ============================================================================
-- SAMPLE DATA
-- ============================================================================

-- Sample clinical staff
INSERT INTO clinical_staff (name, email, role) VALUES
('Dr. Sarah Johnson', 'sarah.johnson@hospital.com', 'surgeon'),
('Nurse Mary Wilson', 'mary.wilson@hospital.com', 'nurse'),
('Care Coordinator Tom Brown', 'tom.brown@hospital.com', 'coordinator');
 