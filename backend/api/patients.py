"""
Patient Management API Endpoints
Handles patient enrollment, retrieval, and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database.connection import get_db
from models import Patient, ClinicalStaff, CallSession
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response
class PatientCreate(BaseModel):
    name: str
    primary_phone_number: str
    secondary_phone_number: Optional[str] = None
    surgery_date: datetime
    primary_physician_id: str
    surgery_type: str = "knee"

class PatientResponse(BaseModel):
    id: str
    name: str
    primary_phone_number: str
    secondary_phone_number: Optional[str] = None
    surgery_date: datetime
    surgery_readiness_status: str
    overall_compliance_score: float
    created_at: datetime

    class Config:
        from_attributes = True

class CallSessionResponse(BaseModel):
    id: str
    call_type: str
    scheduled_date: datetime
    days_from_surgery: int
    call_status: str
    compliance_score: Optional[int] = None
    
    class Config:
        from_attributes = True

@router.post("/enroll", response_model=PatientResponse)
async def enroll_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    """Enroll a new patient and auto-generate call schedule"""
    
    try:
        # Verify physician exists
        physician = db.query(ClinicalStaff).filter(ClinicalStaff.id == patient_data.primary_physician_id).first()
        if not physician:
            raise HTTPException(status_code=400, detail="Physician not found")
        
        # Create patient
        new_patient = Patient(
            name=patient_data.name,
            primary_phone_number=patient_data.primary_phone_number,
            secondary_phone_number=patient_data.secondary_phone_number,
            surgery_date=patient_data.surgery_date,
            primary_physician_id=patient_data.primary_physician_id,
            surgery_readiness_status="pending",
            overall_compliance_score=0.0
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        # Auto-generate call schedule
        call_schedule = [
            (-42, "enrollment"),
            (-28, "education"),
            (-21, "education"),
            (-14, "preparation"),
            (-7, "preparation"),
            (-1, "final_prep")
        ]
        
        for days_from_surgery, call_type in call_schedule:
            scheduled_date = patient_data.surgery_date + timedelta(days=days_from_surgery)
            
            call_session = CallSession(
                patient_id=new_patient.id,
                stage="preop",
                surgery_type=patient_data.surgery_type,
                scheduled_date=scheduled_date,
                days_from_surgery=days_from_surgery,
                call_type=call_type,
                call_status="scheduled"
            )
            
            db.add(call_session)
        
        db.commit()
        
        return PatientResponse.model_validate(new_patient)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enroll patient: {str(e)}")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient details by ID"""
    
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.model_validate(patient)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

@router.get("/{patient_id}/calls", response_model=List[CallSessionResponse])
async def get_patient_calls(patient_id: str, db: Session = Depends(get_db)):
    """Get all calls for a patient"""
    
    try:
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        calls = db.query(CallSession).filter(CallSession.patient_id == patient_id).order_by(CallSession.scheduled_date).all()
        
        return [CallSessionResponse.model_validate(call) for call in calls]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient calls: {str(e)}")

@router.get("/")
async def list_patients(db: Session = Depends(get_db)):
    """List all patients"""
    
    try:
        patients = db.query(Patient).all()
        return [PatientResponse.model_validate(patient) for patient in patients]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patients: {str(e)}")

@router.get("/staff/list")
async def list_clinical_staff(db: Session = Depends(get_db)):
    """List all clinical staff (for enrollment forms)"""
    
    try:
        staff = db.query(ClinicalStaff).all()
        return [
            {
                "id": str(staff_member.id),
                "name": staff_member.name,
                "role": staff_member.role,
                "email": staff_member.email
            }
            for staff_member in staff
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list staff: {str(e)}")
