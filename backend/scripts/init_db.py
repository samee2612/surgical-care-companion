#!/usr/bin/env python3
"""
Database Initialization Script
Sets up the database with tables and sample data
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import create_tables, init_db, check_db_connection
from models import Patient, ClinicalStaff, CallSession
from database.connection import SessionLocal
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize the database with tables and sample data"""
    
    logger.info("Starting database initialization...")
    
    # Check database connection
    if not await check_db_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        
        # Initialize with sample data
        logger.info("Adding sample data...")
        init_db()
        
        # Create sample patient with scheduled calls
        create_sample_patient_with_calls()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


def create_sample_patient_with_calls():
    """Create a sample patient with scheduled calls"""
    
    db = SessionLocal()
    
    try:
        # Check if sample patient already exists
        existing_patient = db.query(Patient).filter(Patient.name == "John Smith").first()
        if existing_patient:
            logger.info("Sample patient already exists")
            return
        
        # Get a physician
        physician = db.query(ClinicalStaff).filter(ClinicalStaff.role == "surgeon").first()
        if not physician:
            logger.warning("No surgeon found, creating one...")
            physician = ClinicalStaff(
                name="Dr. Sarah Johnson",
                email="sarah.johnson@hospital.com",
                role="surgeon"
            )
            db.add(physician)
            db.commit()
        
        # Create sample patient
        surgery_date = datetime.now() + timedelta(days=7)  # Surgery in 7 days
        
        patient = Patient(
            name="John Smith",
            primary_phone_number="+1234567890",
            secondary_phone_number="+1234567891",
            surgery_date=surgery_date,
            primary_physician_id=physician.id,
            surgery_readiness_status="pending",
            overall_compliance_score=75.0
        )
        
        db.add(patient)
        db.commit()
        
        # Create scheduled calls
        call_schedule = [
            (-42, "enrollment"),
            (-28, "education"),
            (-21, "education"),
            (-14, "preparation"),
            (-7, "preparation"),
            (-1, "final_prep")
        ]
        
        for days_from_surgery, call_type in call_schedule:
            scheduled_date = surgery_date + timedelta(days=days_from_surgery)
            
            call_session = CallSession(
                patient_id=patient.id,
                stage="preop",
                surgery_type="knee",
                scheduled_date=scheduled_date,
                days_from_surgery=days_from_surgery,
                call_type=call_type,
                call_status="scheduled"
            )
            
            db.add(call_session)
        
        db.commit()
        logger.info(f"Created sample patient '{patient.name}' with {len(call_schedule)} scheduled calls")
        
    except Exception as e:
        logger.error(f"Failed to create sample patient: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main()) 