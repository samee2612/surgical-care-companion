"""
Patient Management API Endpoints
Handles patient enrollment, retrieval, and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from database.connection import get_db
from models import Patient, VoiceInteraction
from pydantic import BaseModel, ConfigDict

router = APIRouter()

# Pydantic models for request/response
class PatientCreate(BaseModel):
    mrn: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    voice_consent_given: bool = False
    data_consent_given: bool = False

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    mrn: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    voice_consent_given: bool
    data_consent_given: bool
    program_active: bool
    enrollment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class VoiceInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    call_date: datetime
    call_duration: Optional[int] = None
    call_status: Optional[str] = None
    pain_level: Optional[int] = None
    concerns: Optional[str] = None

@router.post("/", response_model=PatientResponse)
async def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    
    try:
        # Create patient
        new_patient = Patient(
            mrn=patient_data.mrn,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            date_of_birth=patient_data.date_of_birth,
            phone=patient_data.phone,
            email=patient_data.email,
            emergency_contact_name=patient_data.emergency_contact_name,
            emergency_contact_phone=patient_data.emergency_contact_phone,
            voice_consent_given=patient_data.voice_consent_given,
            data_consent_given=patient_data.data_consent_given,
            program_active=True,
            enrollment_date=datetime.utcnow()
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        return PatientResponse.model_validate(new_patient)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all patients"""
    
    try:
        patients = db.query(Patient).offset(skip).limit(limit).all()
        return [PatientResponse.model_validate(patient) for patient in patients]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patients: {str(e)}")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get a specific patient by ID"""
    
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.model_validate(patient)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

@router.get("/{patient_id}/voice-interactions", response_model=List[VoiceInteractionResponse])
async def get_patient_voice_interactions(
    patient_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get voice interactions for a specific patient"""
    
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get voice interactions
        interactions = db.query(VoiceInteraction).filter(
            VoiceInteraction.patient_id == patient_id
        ).offset(skip).limit(limit).all()
        
        return [VoiceInteractionResponse.model_validate(interaction) for interaction in interactions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voice interactions: {str(e)}")

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):
    """Update a patient"""
    
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Update patient fields
        for field, value in patient_data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        
        patient.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(patient)
        
        return PatientResponse.model_validate(patient)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update patient: {str(e)}")

@router.delete("/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Delete a patient"""
    
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        db.delete(patient)
        db.commit()
        
        return {"message": "Patient deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")
