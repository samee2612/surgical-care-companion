"""
Test Cases for Call Scheduling Logic
Tests the automatic generation of scheduled calls based on surgery dates
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import uuid
import os

from main import app
from database.connection import get_db
from models import Patient, CallSession, ClinicalStaff
from models.base import Base


# Test database setup - using PostgreSQL for testing
TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/tka_voice_test"


def get_test_db():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create test database if it doesn't exist
    try:
        # Try to create the test database 
        main_engine = create_engine("postgresql://user:password@localhost:5432/postgres", echo=False)
        with main_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            try:
                conn.execute(text("CREATE DATABASE tka_voice_test"))
            except Exception:
                pass  # Database already exists
        main_engine.dispose()
    except Exception as e:
        print(f"Warning: Could not create test database: {e}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


# Test client setup with dependency override
def get_test_client():
    """Get test client with overridden database dependency"""
    test_app = app
    test_app.dependency_overrides[get_db] = get_test_db
    return TestClient(test_app)


client = get_test_client()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create test database if it doesn't exist
    try:
        main_engine = create_engine("postgresql://user:password@localhost:5432/postgres", echo=False)
        with main_engine.connect() as conn:
            conn.execute(text("COMMIT"))
            try:
                conn.execute(text("CREATE DATABASE tka_voice_test"))
            except Exception:
                pass  # Database already exists
        main_engine.dispose()
    except Exception as e:
        print(f"Warning: Could not create test database: {e}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Clean up any existing data
    session.query(CallSession).delete()
    session.query(Patient).delete()
    session.query(ClinicalStaff).delete()
    session.commit()
    
    # Create a test physician
    test_physician = ClinicalStaff(
        id=uuid.uuid4(),
        name="Dr. Test Physician",
        email="test.physician@hospital.com",
        role="surgeon"
    )
    session.add(test_physician)
    session.commit()
    
    # Override the app's database dependency for this test
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Clean up
    session.query(CallSession).delete()
    session.query(Patient).delete()
    session.query(ClinicalStaff).delete()
    session.commit()
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "name": "John Test Patient",
        "primary_phone_number": "+1234567890",
        "secondary_phone_number": "+1234567891",
        "surgery_date": "2024-03-15T10:00:00",
        "surgery_type": "knee"
    }


class TestCallScheduling:
    """Test cases for call scheduling logic"""
    
    def test_correct_number_of_calls_scheduled(self, db_session, sample_patient_data):
        """Test that exactly 6 calls are scheduled for a patient"""
        # Get the test physician
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        # Create patient via API
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        assert response.status_code == 200
        
        patient_data = response.json()
        patient_id = patient_data["id"]
        
        # Check that 6 calls were scheduled
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        assert len(calls) == 6, f"Expected 6 calls, but got {len(calls)}"
    
    def test_call_schedule_dates_calculation(self, db_session, sample_patient_data):
        """Test that call dates are calculated correctly relative to surgery date"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        surgery_date = datetime.fromisoformat(sample_patient_data["surgery_date"].replace("Z", "+00:00"))
        
        # Create patient
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        # Get scheduled calls
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).order_by(CallSession.scheduled_date).all()
        
        # Expected schedule: -42, -28, -21, -14, -7, -1 days from surgery
        expected_days = [-42, -28, -21, -14, -7, -1]
        
        for i, call in enumerate(calls):
            expected_date = surgery_date + timedelta(days=expected_days[i])
            assert call.scheduled_date.date() == expected_date.date(), \
                f"Call {i+1}: Expected {expected_date.date()}, got {call.scheduled_date.date()}"
            assert call.days_from_surgery == expected_days[i], \
                f"Call {i+1}: Expected {expected_days[i]} days, got {call.days_from_surgery}"
    
    def test_call_types_assignment(self, db_session, sample_patient_data):
        """Test that call types are assigned correctly"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        # Create patient
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        # Get scheduled calls ordered by date
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).order_by(CallSession.scheduled_date).all()
        
        # Expected call types in chronological order
        expected_call_types = [
            "enrollment",     # -42 days
            "education",      # -28 days
            "education",      # -21 days
            "preparation",    # -14 days
            "preparation",    # -7 days
            "final_prep"      # -1 day
        ]
        
        for i, call in enumerate(calls):
            assert call.call_type == expected_call_types[i], \
                f"Call {i+1}: Expected {expected_call_types[i]}, got {call.call_type}"
    
    def test_all_calls_marked_as_scheduled(self, db_session, sample_patient_data):
        """Test that all generated calls have 'scheduled' status"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        
        for call in calls:
            assert call.call_status == "scheduled", \
                f"Expected 'scheduled' status, got '{call.call_status}'"
            assert call.stage == "preop", \
                f"Expected 'preop' stage, got '{call.stage}'"
    
    def test_surgery_type_propagation(self, db_session, sample_patient_data):
        """Test that surgery type is correctly set in all call sessions"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        sample_patient_data["surgery_type"] = "hip"  # Different surgery type
        
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        
        for call in calls:
            assert call.surgery_type == "hip", \
                f"Expected 'hip' surgery type, got '{call.surgery_type}'"
    
    def test_different_surgery_dates(self, db_session):
        """Test call scheduling with different surgery dates"""
        physician = db_session.query(ClinicalStaff).first()
        
        test_dates = [
            "2024-01-15T09:00:00",  # January
            "2024-06-30T14:30:00",  # June (mid-year)
            "2024-12-25T11:00:00"   # December (end of year)
        ]
        
        for surgery_date_str in test_dates:
            patient_data = {
                "name": f"Patient {surgery_date_str}",
                "primary_phone_number": "+1234567890",
                "surgery_date": surgery_date_str,
                "primary_physician_id": str(physician.id),
                "surgery_type": "knee"
            }
            
            response = client.post("/api/v1/patients/enroll", json=patient_data)
            assert response.status_code == 200
            
            patient_id = response.json()["id"]
            calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
            
            # Verify 6 calls are created regardless of surgery date
            assert len(calls) == 6, f"Failed for surgery date {surgery_date_str}"
            
            # Verify dates are calculated correctly
            surgery_date = datetime.fromisoformat(surgery_date_str)
            expected_days = [-42, -28, -21, -14, -7, -1]
            
            calls_sorted = sorted(calls, key=lambda x: x.scheduled_date)
            for i, call in enumerate(calls_sorted):
                expected_date = surgery_date + timedelta(days=expected_days[i])
                assert call.scheduled_date.date() == expected_date.date()
    
    def test_weekend_scheduling(self, db_session):
        """Test that calls are scheduled even if they fall on weekends"""
        physician = db_session.query(ClinicalStaff).first()
        
        # Choose a surgery date that will result in some calls on weekends
        # Sunday surgery date
        patient_data = {
            "name": "Weekend Test Patient",
            "primary_phone_number": "+1234567890",
            "surgery_date": "2024-03-17T10:00:00",  # Sunday
            "primary_physician_id": str(physician.id),
            "surgery_type": "knee"
        }
        
        response = client.post("/api/v1/patients/enroll", json=patient_data)
        patient_id = response.json()["id"]
        
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        assert len(calls) == 6, "Should schedule calls even on weekends"
        
        # Verify all calls are still scheduled (no skipping of weekend dates)
        for call in calls:
            assert call.call_status == "scheduled"
    
    def test_call_patient_id_association(self, db_session, sample_patient_data):
        """Test that all calls are correctly associated with the patient"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        # Get the actual patient from database
        patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        
        for call in calls:
            assert str(call.patient_id) == patient_id, \
                "Call should be associated with the correct patient"
            assert call.patient_id == patient.id, \
                "Call patient_id should match patient UUID"
    
    def test_get_patient_calls_endpoint(self, db_session, sample_patient_data):
        """Test the API endpoint for retrieving patient calls"""
        physician = db_session.query(ClinicalStaff).first()
        sample_patient_data["primary_physician_id"] = str(physician.id)
        
        # Create patient
        response = client.post("/api/v1/patients/enroll", json=sample_patient_data)
        patient_id = response.json()["id"]
        
        # Get calls via API
        calls_response = client.get(f"/api/v1/patients/{patient_id}/calls")
        assert calls_response.status_code == 200
        
        calls_data = calls_response.json()
        assert len(calls_data) == 6, "API should return 6 scheduled calls"
        
        # Verify calls are sorted by scheduled_date
        for i in range(len(calls_data) - 1):
            current_date = datetime.fromisoformat(calls_data[i]["scheduled_date"].replace("Z", "+00:00"))
            next_date = datetime.fromisoformat(calls_data[i + 1]["scheduled_date"].replace("Z", "+00:00"))
            assert current_date <= next_date, "Calls should be sorted by scheduled_date"
    
    def test_edge_case_leap_year(self, db_session):
        """Test call scheduling during leap year scenarios"""
        physician = db_session.query(ClinicalStaff).first()
        
        # Surgery on leap day
        patient_data = {
            "name": "Leap Year Patient",
            "primary_phone_number": "+1234567890",
            "surgery_date": "2024-02-29T10:00:00",  # Leap day
            "primary_physician_id": str(physician.id),
            "surgery_type": "knee"
        }
        
        response = client.post("/api/v1/patients/enroll", json=patient_data)
        assert response.status_code == 200
        
        patient_id = response.json()["id"]
        calls = db_session.query(CallSession).filter(CallSession.patient_id == patient_id).all()
        
        assert len(calls) == 6, "Should handle leap year dates correctly"
        
        # Verify earliest call is 42 days before leap day
        earliest_call = min(calls, key=lambda x: x.scheduled_date)
        expected_earliest = datetime(2024, 2, 29) + timedelta(days=-42)
        assert earliest_call.scheduled_date.date() == expected_earliest.date()


# Additional integration test
def test_full_patient_enrollment_flow(db_session):
    """Integration test for complete patient enrollment and call scheduling"""
    physician = db_session.query(ClinicalStaff).first()
    
    patient_data = {
        "name": "Integration Test Patient",
        "primary_phone_number": "+1555123456",
        "secondary_phone_number": "+1555123457",
        "surgery_date": "2024-08-15T13:30:00",
        "primary_physician_id": str(physician.id),
        "surgery_type": "knee"
    }
    
    # Step 1: Enroll patient
    enroll_response = client.post("/api/v1/patients/enroll", json=patient_data)
    assert enroll_response.status_code == 200
    
    patient_response_data = enroll_response.json()
    patient_id = patient_response_data["id"]
    
    # Step 2: Verify patient data
    assert patient_response_data["name"] == patient_data["name"]
    assert patient_response_data["surgery_readiness_status"] == "pending"
    assert patient_response_data["overall_compliance_score"] == 0.0
    
    # Step 3: Get patient calls
    calls_response = client.get(f"/api/v1/patients/{patient_id}/calls")
    assert calls_response.status_code == 200
    
    calls = calls_response.json()
    assert len(calls) == 6
    
    # Step 4: Verify call sequence
    expected_sequence = [
        (-42, "enrollment"),
        (-28, "education"),
        (-21, "education"),
        (-14, "preparation"),
        (-7, "preparation"),
        (-1, "final_prep")
    ]
    
    surgery_date = datetime.fromisoformat(patient_data["surgery_date"])
    
    for i, (expected_days, expected_type) in enumerate(expected_sequence):
        call = calls[i]
        expected_call_date = surgery_date + timedelta(days=expected_days)
        
        assert call["days_from_surgery"] == expected_days
        assert call["call_type"] == expected_type
        assert call["call_status"] == "scheduled"
        
        call_date = datetime.fromisoformat(call["scheduled_date"].replace("Z", "+00:00"))
        assert call_date.date() == expected_call_date.date()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 