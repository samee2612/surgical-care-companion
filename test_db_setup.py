#!/usr/bin/env python3
"""
Test script to set up database and create test data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.connection import create_tables, get_db
from backend.models import Patient, ClinicalStaff, CallSession
from datetime import datetime, timedelta
import uuid

def test_database_setup():
    """Test database connection and create tables"""
    print("🔧 Setting up database...")
    
    try:
        # Create tables
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Test database connection
        db = next(get_db())
        
        # Create a test clinical staff member
        staff_id = uuid.uuid4()
        test_staff = ClinicalStaff(
            id=staff_id,
            name="Dr. Test Doctor",
            email="test@example.com",
            role="surgeon"
        )
        
        # Create a test patient
        patient_id = uuid.uuid4()
        test_patient = Patient(
            id=patient_id,
            name="Bob Martinez",
            primary_phone_number="+1234567890",
            surgery_date=datetime.now() + timedelta(days=30),
            primary_physician_id=staff_id
        )
        
        # Create a test call session
        call_session = CallSession(
            patient_id=patient_id,
            stage="preop",
            scheduled_date=datetime.now() + timedelta(days=15),
            days_from_surgery=-15,
            call_type="education"
        )
        
        # Add to database in the correct order (staff first, then patient, then call session)
        db.add(test_staff)
        db.commit()  # Commit staff first
        
        db.add(test_patient)
        db.commit()  # Commit patient second
        
        db.add(call_session)
        db.commit()  # Commit call session last
        
        print(f"✅ Test data created:")
        print(f"   - Patient: {test_patient.name} (ID: {test_patient.id})")
        print(f"   - Call Session: {call_session.call_type} (ID: {call_session.id})")
        print(f"   - Staff: {test_staff.name} (ID: {test_staff.id})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_setup() 