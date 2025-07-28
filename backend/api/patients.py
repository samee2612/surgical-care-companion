"""
Patient Management API Endpoints
Handles patient enrollment, retrieval, and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Union, Any
from datetime import datetime, timedelta
import uuid

from pydantic import BaseModel, ConfigDict
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

# Pydantic models for request/response
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    primary_phone: str
    secondary_phone: Optional[str] = None
    surgery_readiness_status: str = "pending"
    surgery_date: datetime

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Union[str, uuid.UUID]
    name: str
    primary_phone_number: str
    secondary_phone_number: Optional[str] = None
    surgery_date: datetime
    surgery_readiness_status: str
    overall_compliance_score: float
    created_at: datetime

class CallSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Union[str, uuid.UUID]
    call_type: str
    scheduled_date: datetime
    days_from_surgery: int
    call_status: str
    compliance_score: Optional[int] = None

@router.post("/enroll", response_model=PatientResponse)
async def enroll_patient(patient_data: PatientCreate):
    """Enroll a new patient and auto-generate call schedule"""
    try:
        conn = psycopg2.connect(
            dbname="tka_voice",
            user="user",
            password="password",
            host="postgres",  # Docker Compose service name
            port=5432
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Insert patient
        cur.execute(
            """
            INSERT INTO patients (first_name, last_name, date_of_birth, primary_phone, secondary_phone, surgery_readiness_status, surgery_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, first_name, last_name, date_of_birth, primary_phone, secondary_phone, surgery_readiness_status, surgery_date, created_at;
            """,
            (
                patient_data.first_name,
                patient_data.last_name,
                patient_data.date_of_birth,
                patient_data.primary_phone,
                patient_data.secondary_phone,
                patient_data.surgery_readiness_status,
                patient_data.surgery_date
            )
        )
        patient = cur.fetchone()
        patient_id = patient["id"]
        # Schedule the three calls
        call_types = {
            "initial_clinical_assessment": timedelta(weeks=4),
            "preparation": timedelta(weeks=2),
            "final_logistics": timedelta(weeks=1)
        }

        for call_name, time_before_surgery in call_types.items():
            scheduled_date = patient_data.surgery_date - time_before_surgery
            days_from_surgery = (scheduled_date - patient_data.surgery_date).days

            cur.execute(
                """
                INSERT INTO call_sessions (patient_id, call_type, scheduled_date, days_from_surgery, stage, surgery_type)
                VALUES (%s, %s, %s, %s, 'preop', 'knee');
                """,
                (patient_id, call_name, scheduled_date, days_from_surgery)
            )

        conn.commit()
        cur.close()
        conn.close()
        return PatientResponse.model_validate({
            "id": patient["id"],
            "name": f"{patient['first_name']} {patient['last_name']}",
            "primary_phone_number": patient["primary_phone"],
            "secondary_phone_number": patient["secondary_phone"],
            "surgery_date": patient["surgery_date"],
            "surgery_readiness_status": patient["surgery_readiness_status"],
            "overall_compliance_score": 0.0,
            "created_at": patient["created_at"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enroll patient: {str(e)}")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get patient details by ID"""
    
    try:
        # [Database access code stubbed out]
        # patient = db.query(Patient).filter(Patient.id == patient_id).first()
        # if not patient:
        #     raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.model_validate({
            "id": uuid.UUID(patient_id),
            "name": "Patient Name",
            "primary_phone_number": "123-456-7890",
            "secondary_phone_number": None,
            "surgery_date": datetime.now(),
            "surgery_readiness_status": "ready",
            "overall_compliance_score": 0.95,
            "created_at": datetime.now()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

@router.get("/{patient_id}/calls", response_model=List[CallSessionResponse])
async def get_patient_calls(patient_id: str):
    """Get all calls for a patient"""
    
    try:
        # Verify patient exists
        # [Database access code stubbed out]
        # patient = db.query(Patient).filter(Patient.id == patient_id).first()
        # if not patient:
        #     raise HTTPException(status_code=404, detail="Patient not found")
        
        # [Database access code stubbed out]
        calls = [
            {
                "id": uuid.uuid4(),
                "call_type": "initial_clinical_assessment",
                "scheduled_date": datetime.now() - timedelta(days=35),
                "days_from_surgery": -35,
                "call_status": "completed",
                "compliance_score": 95
            },
            {
                "id": uuid.uuid4(),
                "call_type": "education",
                "scheduled_date": datetime.now() - timedelta(days=28),
                "days_from_surgery": -28,
                "call_status": "scheduled",
                "compliance_score": None
            },
            {
                "id": uuid.uuid4(),
                "call_type": "preparation",
                "scheduled_date": datetime.now() - timedelta(days=21),
                "days_from_surgery": -21,
                "call_status": "scheduled",
                "compliance_score": None
            },
            {
                "id": uuid.uuid4(),
                "call_type": "education",
                "scheduled_date": datetime.now() - timedelta(days=14),
                "days_from_surgery": -14,
                "call_status": "scheduled",
                "compliance_score": None
            },
            {
                "id": uuid.uuid4(),
                "call_type": "education",
                "scheduled_date": datetime.now() - timedelta(days=7),
                "days_from_surgery": -7,
                "call_status": "scheduled",
                "compliance_score": None
            },
            {
                "id": uuid.uuid4(),
                "call_type": "final_prep",
                "scheduled_date": datetime.now() - timedelta(days=1),
                "days_from_surgery": -1,
                "call_status": "scheduled",
                "compliance_score": None
            }
        ]
        
        return [CallSessionResponse.model_validate(call) for call in calls]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient calls: {str(e)}")

@router.get("/")
async def list_patients():
    """List all patients"""
    
    try:
        # [Database access code stubbed out]
        patients = [
            {
                "id": uuid.uuid4(),
                "name": "Patient A",
                "primary_phone_number": "111-222-3333",
                "secondary_phone_number": "444-555-6666",
                "surgery_date": datetime.now() - timedelta(days=30),
                "surgery_readiness_status": "ready",
                "overall_compliance_score": 0.98,
                "created_at": datetime.now() - timedelta(days=10)
            },
            {
                "id": uuid.uuid4(),
                "name": "Patient B",
                "primary_phone_number": "777-888-9999",
                "secondary_phone_number": None,
                "surgery_date": datetime.now() - timedelta(days=60),
                "surgery_readiness_status": "pending",
                "overall_compliance_score": 0.85,
                "created_at": datetime.now() - timedelta(days=20)
            }
        ]
        return [PatientResponse.model_validate(patient) for patient in patients]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patients: {str(e)}")

@router.get("/staff/list")
async def list_clinical_staff():
    """List all clinical staff (for enrollment forms)"""
    
    try:
        # [Database access code stubbed out]
        staff = [
            {
                "id": uuid.uuid4(),
                "name": "Dr. Smith",
                "role": "Orthopedic Surgeon",
                "email": "dr.smith@example.com"
            },
            {
                "id": uuid.uuid4(),
                "name": "Nurse Johnson",
                "role": "Nurse",
                "email": "nurse.johnson@example.com"
            }
        ]
        return [
            {
                "id": str(staff_member["id"]),
                "name": staff_member["name"],
                "role": staff_member["role"],
                "email": staff_member["email"]
            }
            for staff_member in staff
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list staff: {str(e)}")
