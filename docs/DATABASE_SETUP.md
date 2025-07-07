# TKA Voice Agent Database Setup Guide

This guide explains how to set up and manage the PostgreSQL database for the TKA Voice Agent application.

## Quick Start

### Automated Setup (Recommended)

```bash
# 1. Run the automated setup script
./scripts/setup_database.sh

# 2. Start the application
docker-compose up -d
```

### Manual Setup

```bash
# 1. Start PostgreSQL
docker-compose up -d postgres

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Initialize database
python scripts/init_db.py
```

## Database Architecture

### Simplified Schema (3 Tables)

Our database uses a simplified 3-table architecture:

1. **clinical_staff** - Healthcare providers (surgeons, nurses, coordinators)
2. **patients** - Patient information with readiness tracking
3. **call_sessions** - Scheduled and completed voice calls

### Key Features

- **PostgreSQL UUID Primary Keys** - Using `gen_random_uuid()` for secure identifiers
- **Automated Call Scheduling** - Calls auto-generated based on surgery dates
- **Compliance Tracking** - Patient readiness scores and compliance monitoring
- **AI Agent Notes** - Structured summaries stored in `call_sessions.agent_notes`

## Database Schema Details

### Patients Table
```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    primary_phone_number VARCHAR(20) NOT NULL,
    secondary_phone_number VARCHAR(20),
    surgery_date TIMESTAMP NOT NULL,
    primary_physician_id UUID NOT NULL REFERENCES clinical_staff(id),
    surgery_readiness_status VARCHAR(30) NOT NULL DEFAULT 'done',
    overall_compliance_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Call Sessions Table
```sql
CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    stage VARCHAR(50) NOT NULL, -- 'preop/postop'
    surgery_type VARCHAR(50) NOT NULL, -- 'knee', 'hip', etc.
    scheduled_date TIMESTAMP NOT NULL,
    days_from_surgery INTEGER NOT NULL, -- -42, -28, -21, -14, -7, -1
    call_type VARCHAR(50) NOT NULL, -- 'enrollment', 'education', 'preparation', 'final_prep'
    call_status VARCHAR(30) NOT NULL DEFAULT 'scheduled',
    agent_notes TEXT, -- AI-generated structured summaries
    compliance_score INTEGER, -- 0-100 call score
    concerns_identified TEXT[], -- Array of concerns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Call Scheduling Logic

### Pre-Surgery Timeline
- **Week 6 (-42 days)**: Initial enrollment call
- **Week 4 (-28 days)**: Education call
- **Week 3 (-21 days)**: Education call
- **Week 2 (-14 days)**: Preparation call
- **Week 1 (-7 days)**: Preparation call
- **Day -1**: Final preparation call

### Auto-Generation
When a patient is enrolled, the system automatically creates all scheduled calls:

```python
# Example: Patient with surgery on 2024-01-15
call_schedule = [
    (-42, "enrollment"),    # 2023-12-04
    (-28, "education"),     # 2023-12-18
    (-21, "education"),     # 2023-12-25
    (-14, "preparation"),   # 2024-01-01
    (-7, "preparation"),    # 2024-01-08
    (-1, "final_prep")      # 2024-01-14
]
```

## Environment Setup

### Local Development

1. **Environment Variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
DATABASE_URL=postgresql://tka_user:tka_password@localhost:5432/tka_voice_db
```

2. **Docker Compose**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tka_voice_db
      POSTGRES_USER: tka_user
      POSTGRES_PASSWORD: tka_password
    ports:
      - "5432:5432"
```

### Production Deployment

1. **Environment Variables**
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
export ENVIRONMENT="production"
export DEBUG="false"
```

2. **Migration Commands**
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"
```

## Database Operations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column"

# Create empty migration
alembic revision -m "Custom migration"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Sample Data Management

```python
# Initialize database with sample data
python backend/scripts/init_db.py

# Create sample patient with calls
from backend.models import Patient, CallSession
from backend.database.connection import SessionLocal

def create_sample_patient():
    db = SessionLocal()
    
    # Create patient
    patient = Patient(
        name="John Smith",
        primary_phone_number="+1234567890",
        surgery_date=datetime.now() + timedelta(days=7),
        primary_physician_id=physician_id
    )
    
    # Auto-generate scheduled calls
    # ... (see init_db.py for full example)
```

### Database Queries

```python
# Get patients ready for surgery
ready_patients = db.query(Patient).filter(
    Patient.surgery_readiness_status == "done",
    Patient.overall_compliance_score >= 80
).all()

# Get today's scheduled calls
today_calls = db.query(CallSession).filter(
    CallSession.scheduled_date.date() == datetime.now().date(),
    CallSession.call_status == "scheduled"
).all()

# Get patient with call history
patient_with_calls = db.query(Patient).options(
    joinedload(Patient.call_sessions)
).filter(Patient.id == patient_id).first()
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Start PostgreSQL
docker-compose up -d postgres

# Check connection
pg_isready -h localhost -p 5432
```

2. **Migration Errors**
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Reset to specific migration
alembic downgrade <revision_id>
```

3. **Import Errors**
```bash
# Install missing dependencies
pip install -r backend/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Database Monitoring

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check recent calls
SELECT 
    p.name,
    cs.call_type,
    cs.scheduled_date,
    cs.call_status
FROM call_sessions cs
JOIN patients p ON cs.patient_id = p.id
WHERE cs.scheduled_date >= NOW() - INTERVAL '7 days'
ORDER BY cs.scheduled_date DESC;
```

## Security Considerations

1. **Database Credentials**
   - Never commit credentials to version control
   - Use environment variables for all sensitive data
   - Rotate passwords regularly

2. **Connection Security**
   - Use SSL connections in production
   - Limit database access to application servers only
   - Monitor connection attempts

3. **Data Privacy**
   - Patient data is PHI (Protected Health Information)
   - Implement proper audit logging
   - Follow HIPAA compliance guidelines

## Performance Optimization

### Database Indexes

The schema includes optimized indexes:
```sql
-- Patient indexes
CREATE INDEX idx_patients_primary_phone ON patients(primary_phone_number);
CREATE INDEX idx_patients_surgery_date ON patients(surgery_date);

-- Call session indexes
CREATE INDEX idx_call_sessions_scheduled_date ON call_sessions(scheduled_date);
CREATE INDEX idx_call_sessions_status ON call_sessions(call_status);
```

### Query Optimization

```python
# Use eager loading for relationships
patients_with_calls = db.query(Patient).options(
    joinedload(Patient.call_sessions),
    joinedload(Patient.primary_physician)
).all()

# Filter efficiently
upcoming_calls = db.query(CallSession).filter(
    CallSession.scheduled_date.between(start_date, end_date),
    CallSession.call_status == "scheduled"
).order_by(CallSession.scheduled_date).all()
```

## Backup and Recovery

### Automated Backups

```bash
# Create database backup
pg_dump -h localhost -U tka_user -d tka_voice_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -h localhost -U tka_user -d tka_voice_db < backup_file.sql
```

### Docker Volume Backup

```bash
# Backup PostgreSQL data volume
docker run --rm -v tka_postgres_data:/data -v $(pwd):/backup busybox tar czf /backup/postgres_backup.tar.gz /data

# Restore PostgreSQL data volume
docker run --rm -v tka_postgres_data:/data -v $(pwd):/backup busybox tar xzf /backup/postgres_backup.tar.gz -C /
```

---

## Next Steps

1. **Install Dependencies**: `pip install -r backend/requirements.txt`
2. **Run Setup Script**: `./scripts/setup_database.sh`
3. **Start Application**: `docker-compose up -d`
4. **Access API Docs**: http://localhost:8000/docs

For more information, see the main [README.md](../README.md) file. 