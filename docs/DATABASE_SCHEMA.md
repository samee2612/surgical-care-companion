# 🏥 Surgical Care Companion - Database Schema Documentation

## Overview

The Surgical Care Companion uses a PostgreSQL database to manage patient data, surgical procedures, voice interactions, alerts, and system configuration. This document provides a comprehensive overview of the database schema, relationships, and data flow.

## 🗄️ Database Tables

### Core Tables

#### 1. **users** - Healthcare Providers & Administrators
Stores information about healthcare providers, administrators, and system users.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar (PK) | Unique user identifier |
| `email` | varchar (unique) | User email address |
| `first_name` | varchar | User's first name |
| `last_name` | varchar | User's last name |
| `profile_image_url` | varchar | URL to profile image |
| `role` | varchar | User role: 'provider', 'admin', 'patient' |
| `created_at` | timestamp | Record creation timestamp |
| `updated_at` | timestamp | Last update timestamp |

#### 2. **patients** - Patient Information
Central patient registry with contact information and consent status.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing patient ID |
| `mrn` | varchar (unique) | Medical Record Number |
| `first_name` | varchar | Patient's first name |
| `last_name` | varchar | Patient's last name |
| `date_of_birth` | date | Patient's birth date |
| `phone` | varchar | Primary phone number |
| `email` | varchar | Email address |
| `emergency_contact_name` | varchar | Emergency contact person |
| `emergency_contact_phone` | varchar | Emergency contact phone |
| `voice_consent_given` | boolean | Voice interaction consent |
| `data_consent_given` | boolean | Data usage consent |
| `program_active` | boolean | Program enrollment status |
| `enrollment_date` | timestamp | Program enrollment date |
| `created_at` | timestamp | Record creation timestamp |
| `updated_at` | timestamp | Last update timestamp |

#### 3. **surgeries** - Surgical Procedures
Details about surgical procedures for each patient.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing surgery ID |
| `patient_id` | integer (FK) | Reference to patients table |
| `procedure` | varchar | Name of surgical procedure |
| `surgeon_name` | varchar | Operating surgeon name |
| `surgery_date` | date | Date of surgery |
| `discharge_date` | date | Hospital discharge date |
| `expected_recovery_weeks` | integer | Expected recovery duration |
| `specialty` | varchar | Medical specialty (orthopedic, cardiac, general, neuro) |
| `notes` | text | Additional surgical notes |
| `created_at` | timestamp | Record creation timestamp |
| `updated_at` | timestamp | Last update timestamp |

#### 4. **voice_interactions** - AI Voice Call Records
Records of automated voice interactions with patients.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing interaction ID |
| `patient_id` | integer (FK) | Reference to patients table |
| `surgery_id` | integer (FK) | Reference to surgeries table |
| `call_date` | timestamp | Date and time of call |
| `duration` | integer | Call duration in seconds |
| `transcript` | text | Call transcript |
| `symptoms` | jsonb | Array of detected symptoms |
| `pain_level` | integer | Patient-reported pain level (1-10) |
| `risk_score` | decimal | AI-calculated risk score |
| `status` | varchar | Call status (completed, failed, escalated, normal) |
| `escalated` | boolean | Whether call was escalated |
| `escalation_reason` | text | Reason for escalation |
| `ai_analysis` | jsonb | AI analysis results |
| `call_successful` | boolean | Whether call completed successfully |
| `created_at` | timestamp | Record creation timestamp |

#### 5. **alerts** - Clinical Alerts & Notifications
System-generated alerts based on patient interactions and risk scores.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing alert ID |
| `patient_id` | integer (FK) | Reference to patients table |
| `voice_interaction_id` | integer (FK) | Reference to voice_interactions table |
| `priority` | varchar | Alert priority (high, medium, low) |
| `status` | varchar | Alert status (active, resolved, dismissed) |
| `title` | varchar | Alert title/summary |
| `description` | text | Detailed alert description |
| `risk_score` | decimal | Associated risk score |
| `assigned_provider_id` | varchar (FK) | Assigned healthcare provider |
| `resolved_at` | timestamp | Resolution timestamp |
| `resolved_by` | varchar (FK) | User who resolved alert |
| `created_at` | timestamp | Alert creation timestamp |
| `updated_at` | timestamp | Last update timestamp |

### Supporting Tables

#### 6. **knowledge_articles** - Clinical Knowledge Base
Stores clinical protocols, patient education materials, and system documentation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing article ID |
| `title` | varchar | Article title |
| `content` | text | Article content |
| `category` | varchar | Category (clinical, patient-education, technical, faq, ai-models) |
| `specialty` | varchar | Medical specialty if applicable |
| `tags` | jsonb | Array of searchable tags |
| `author_id` | varchar (FK) | Reference to users table |
| `published` | boolean | Publication status |
| `reading_level` | varchar | Reading level (elementary, middle, high) |
| `language` | varchar | Content language |
| `version` | varchar | Version number |
| `created_at` | timestamp | Record creation timestamp |
| `updated_at` | timestamp | Last update timestamp |

#### 7. **system_settings** - Configuration Management
System-wide configuration settings and parameters.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing setting ID |
| `key` | varchar (unique) | Setting key identifier |
| `value` | jsonb | Setting value (supports complex objects) |
| `description` | text | Setting description |
| `category` | varchar | Setting category (alerts, twilio, billing, ai) |
| `updated_by` | varchar (FK) | User who last updated setting |
| `updated_at` | timestamp | Last update timestamp |

#### 8. **test_simulations** - Testing & Validation
Records of system testing and simulation runs.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Auto-incrementing simulation ID |
| `tester_id` | varchar (FK) | Reference to users table |
| `patient_profile` | varchar | Test patient profile type |
| `injected_symptoms` | jsonb | Simulated symptoms |
| `custom_symptoms` | text | Custom symptom descriptions |
| `resulting_risk_score` | decimal | Calculated risk score |
| `ai_decision` | varchar | AI decision outcome |
| `transcript` | text | Simulated conversation transcript |
| `detected_symptoms` | jsonb | AI-detected symptoms |
| `escalation_triggered` | boolean | Whether escalation was triggered |
| `created_at` | timestamp | Simulation timestamp |

#### 9. **sessions** - User Session Management
Manages user authentication sessions (required for Replit Auth).

| Column | Type | Description |
|--------|------|-------------|
| `sid` | varchar (PK) | Session identifier |
| `sess` | jsonb | Session data |
| `expire` | timestamp | Session expiration time |

## 🔗 Database Relationships

### Primary Relationships

```
users (1) ←→ (many) alerts [assigned_provider_id]
users (1) ←→ (many) alerts [resolved_by]
users (1) ←→ (many) knowledge_articles [author_id]
users (1) ←→ (many) test_simulations [tester_id]
users (1) ←→ (many) system_settings [updated_by]

patients (1) ←→ (many) surgeries [patient_id]
patients (1) ←→ (many) voice_interactions [patient_id]
patients (1) ←→ (many) alerts [patient_id]

surgeries (1) ←→ (many) voice_interactions [surgery_id]

voice_interactions (1) ←→ (many) alerts [voice_interaction_id]
```

### Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    users    │────→│   alerts    │←────│  patients   │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─┬───────────┘
       │                    ↑               │
       │                    │               │
       ↓                    │               ↓
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│knowledge_   │     │voice_       │     │ surgeries   │
│articles     │     │interactions │←────│             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 📊 Sample Data Overview

The database is seeded with realistic test data including:

- **3 Healthcare Providers**: Dr. Sarah Johnson (Orthopedic), Dr. Michael Smith (Cardiac/General), Lisa Chen (Admin)
- **10 Patients**: Diverse ages and surgical procedures
- **10 Surgeries**: Various specialties including:
  - Orthopedic: Knee replacement, Hip replacement, Rotator cuff repair, Spinal fusion
  - Cardiac: Coronary artery bypass graft
  - General: Cholecystectomy, Appendectomy, Hernia repair
  - Other: Cataract surgery, Partial mastectomy
- **5 Voice Interactions**: Realistic conversation transcripts with varying risk levels
- **3 Clinical Alerts**: Including one high-priority infection alert
- **3 Knowledge Articles**: Clinical guidelines and patient education materials

## 🔧 Database Management

### Environment Configuration

The database connection is configured through environment variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/tka_voice
```

### Schema Management

- **ORM**: Drizzle ORM for type-safe database operations
- **Migrations**: Use `npm run db:push` to sync schema changes
- **Seeding**: Run `npx tsx --env-file=.env scripts/seed-database.ts` to populate test data

### Key Indexes

- `patients.mrn` - Unique index for medical record numbers
- `voice_interactions.patient_id` - Foreign key index
- `alerts.patient_id` - Foreign key index
- `sessions.expire` - Session cleanup index

## 🚀 API Integration

The database supports the following API endpoints:

### Patient Management
- `GET /api/patients` - List patients with pagination and search
- `GET /api/patients/:id` - Get specific patient details
- `POST /api/patients` - Create new patient
- `PUT /api/patients/:id` - Update patient information

### Surgery Management
- `GET /api/patients/:id/surgeries` - Get patient surgeries
- `POST /api/surgeries` - Create surgery record

### Voice Interactions
- `GET /api/patients/:id/voice-interactions` - Get patient call history
- `POST /api/voice-interactions` - Record new interaction

### Clinical Alerts
- `GET /api/alerts` - List active alerts
- `GET /api/patients/:id/alerts` - Get patient-specific alerts
- `POST /api/alerts` - Create new alert
- `PUT /api/alerts/:id` - Update alert status

### Knowledge Base
- `GET /api/knowledge` - Search knowledge articles
- `POST /api/knowledge` - Create new article

## 🔒 Data Security & Privacy

- **HIPAA Compliance**: All patient data is stored securely
- **Consent Tracking**: Voice and data consent flags for each patient
- **Audit Trail**: Created/updated timestamps on all records
- **Access Control**: Role-based access through user roles
- **Session Management**: Secure session handling with expiration

## 📈 Performance Considerations

- **Indexing**: Strategic indexes on frequently queried columns
- **JSON Storage**: Efficient JSONB storage for flexible data (symptoms, analysis)
- **Connection Pooling**: PostgreSQL connection pooling for scalability
- **Query Optimization**: Drizzle ORM provides optimized queries

## 🧪 Testing & Development

- **Mock Data**: Comprehensive seed data for development testing
- **Test Simulations**: Dedicated table for system testing records
- **Environment Isolation**: Separate databases for dev/staging/production
- **Schema Validation**: TypeScript types generated from schema
