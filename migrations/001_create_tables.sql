-- Migration: Create main tables for HealthSenseCare

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE clinical_staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    role VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mrn VARCHAR NOT NULL UNIQUE,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    date_of_birth DATE NOT NULL,
    primary_phone VARCHAR NOT NULL,
    secondary_phone VARCHAR,
    email VARCHAR,
    voice_consent_given BOOLEAN DEFAULT FALSE,
    data_consent_given BOOLEAN DEFAULT FALSE,
    surgery_date TIMESTAMP,
    primary_physician_id UUID REFERENCES clinical_staff(id),
    surgery_readiness_status VARCHAR DEFAULT 'pending',
    report JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    stage VARCHAR(50),
    surgery_type VARCHAR(50),
    scheduled_date TIMESTAMP NOT NULL,
    days_from_surgery INTEGER NOT NULL,
    call_type VARCHAR(50) NOT NULL,
    call_status VARCHAR(30) DEFAULT 'scheduled',
    actual_call_start TIMESTAMP,
    call_duration_seconds INTEGER,
    call_outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE patient_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    call_session_id UUID REFERENCES call_sessions(id),
    insight_type VARCHAR NOT NULL,
    insight_data JSON,
    confidence_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
); 