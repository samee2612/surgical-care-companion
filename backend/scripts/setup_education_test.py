#!/usr/bin/env python3
"""
Education Calls Test Setup
Creates test patients with education calls for testing the weekly education system
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Patient, ClinicalStaff, CallSession
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_education_test_patients():
    """Create test patients for education call testing"""
    
    db = SessionLocal()
    
    try:
        # Get or create physician
        physician = db.query(ClinicalStaff).first()
        if not physician:
            physician = ClinicalStaff(
                name="Dr. Sarah Wilson",
                email="sarah.wilson@hospital.com", 
                role="surgeon"
            )
            db.add(physician)
            db.flush()  # Get the ID
        
        # Create test patients for each education week
        test_patients = [
            {
                "name": "Alice Johnson", 
                "surgery_days": 28,  # Week 4 education
                "description": "Week 4 - Surgery Overview"
            },
            {
                "name": "Bob Martinez",
                "surgery_days": 21,  # Week 3 education  
                "description": "Week 3 - Home Preparation"
            },
            {
                "name": "Carol Davis",
                "surgery_days": 14,  # Week 2 education
                "description": "Week 2 - Pain Management" 
            },
            {
                "name": "David Brown",
                "surgery_days": 7,   # Week 1 education
                "description": "Week 1 - Hospital Stay"
            }
        ]
        
        created_patients = []
        
        for patient_info in test_patients:
            # Check if patient already exists
            existing = db.query(Patient).filter(Patient.name == patient_info["name"]).first()
            if existing:
                logger.info(f"Patient {patient_info['name']} already exists")
                continue
            
            # Create patient
            surgery_date = datetime.now() + timedelta(days=patient_info["surgery_days"])
            
            patient = Patient(
                name=patient_info["name"],
                primary_phone_number=f"+155512345{len(created_patients)}",
                surgery_date=surgery_date,
                primary_physician_id=physician.id,
                surgery_readiness_status="pending",
                overall_compliance_score=0.0
            )
            
            db.add(patient)
            db.flush()  # Get the ID
            
            # Create ONLY the specific education call for testing
            call_session = CallSession(
                patient_id=patient.id,
                stage="preop", 
                surgery_type="knee",
                scheduled_date=datetime.now(),  # Available now for testing
                days_from_surgery=-patient_info["surgery_days"],
                call_type="education",
                call_status="scheduled"
            )
            
            db.add(call_session)
            created_patients.append({
                "patient": patient,
                "call_session": call_session,
                "description": patient_info["description"]
            })
        
        db.commit()
        
        # Print test instructions
        print("\n" + "="*60)
        print("🎓 EDUCATION CALLS TEST SETUP COMPLETE")
        print("="*60)
        
        for i, info in enumerate(created_patients):
            patient = info["patient"]
            call = info["call_session"]
            print(f"\n{i+1}. {info['description']}")
            print(f"   Patient: {patient.name}")
            print(f"   Patient ID: {patient.id}")
            print(f"   Call Session ID: {call.id}")
            print(f"   Days from Surgery: {call.days_from_surgery}")
        
        print(f"\n🔧 TEST INSTRUCTIONS:")
        print(f"1. Start the backend server: python main.py")
        print(f"2. Test each education call using the /start-call endpoint")
        print(f"3. Or use the frontend demo with the patient IDs above")
        
        print(f"\n📞 API EXAMPLE:")
        if created_patients:
            example_patient = created_patients[0]
            print(f"POST /api/v1/voice/start-call")
            print(f"{{")
            print(f'  "patient_id": "{example_patient["patient"].id}",')
            print(f'  "call_session_id": "{example_patient["call_session"].id}"')
            print(f"}}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to setup education test: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_complete_education_patient():
    """Create one patient with all 4 education calls scheduled"""
    
    db = SessionLocal()
    
    try:
        # Check if already exists
        existing = db.query(Patient).filter(Patient.name == "Emma Thompson").first()
        if existing:
            logger.info("Complete education patient already exists")
            return
        
        physician = db.query(ClinicalStaff).first()
        if not physician:
            raise ValueError("No physician found. Please run database initialization first.")
        
        surgery_date = datetime.now() + timedelta(days=35)  # Surgery in 5 weeks
        
        patient = Patient(
            name="Emma Thompson",
            primary_phone_number="+15551234567", 
            surgery_date=surgery_date,
            primary_physician_id=physician.id,
            surgery_readiness_status="pending",
            overall_compliance_score=0.0
        )
        
        db.add(patient)
        db.flush()
        
        # Create all 4 education calls
        education_schedule = [
            (-35, "enrollment", "Enrollment Assessment"),
            (-28, "education", "Week 4: Surgery Overview"),
            (-21, "education", "Week 3: Home Preparation"),
            (-14, "education", "Week 2: Pain Management"),
            (-7, "education", "Week 1: Hospital Stay"),
            (-1, "final_prep", "Final Preparation")
        ]
        
        call_sessions = []
        for days, call_type, description in education_schedule:
            scheduled_date = surgery_date + timedelta(days=days)
            
            call_session = CallSession(
                patient_id=patient.id,
                stage="preop",
                surgery_type="knee", 
                scheduled_date=scheduled_date,
                days_from_surgery=days,
                call_type=call_type,
                call_status="scheduled"
            )
            
            db.add(call_session)
            call_sessions.append((call_session, description))
        
        db.commit()
        
        print(f"\n🎯 COMPLETE EDUCATION JOURNEY PATIENT")
        print(f"Patient: {patient.name}")
        print(f"Patient ID: {patient.id}")
        print(f"Surgery Date: {surgery_date.strftime('%Y-%m-%d')}")
        print(f"\nScheduled Calls:")
        
        for call, description in call_sessions:
            status_icon = "📞" if call.call_type == "education" else "📋"
            print(f"  {status_icon} {description}")
            print(f"     Call ID: {call.id} | Days: {call.days_from_surgery}")
        
    except Exception as e:
        logger.error(f"Failed to create complete education patient: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Setting up education call tests...")
    setup_education_test_patients()
    create_complete_education_patient()
    logger.info("Education test setup complete!") 