"""
Patient Management Service
Business logic for patient operations, enrollment, and data management.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from models import Patient, ClinicalStaff, CallSession
from database.connection import get_db

logger = logging.getLogger(__name__)


class PatientService:
    """Service for managing patient operations"""
    
    def __init__(self):
        self.logger = logger
    
    def create_patient(
        self, 
        db: Session,
        first_name: str,
        last_name: str,
        phone_number: str,
        date_of_birth: datetime,
        medical_record_number: str,
        **kwargs
    ) -> Patient:
        """Create a new patient record"""
        
        try:
            # Check if patient already exists
            existing = db.query(Patient).filter(
                (Patient.phone_number == phone_number) |
                (Patient.medical_record_number == medical_record_number)
            ).first()
            
            if existing:
                raise ValueError(f"Patient already exists with phone {phone_number} or MRN {medical_record_number}")
            
            # Create new patient
            patient = Patient(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                date_of_birth=date_of_birth,
                medical_record_number=medical_record_number,
                **kwargs
            )
            
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
            self.logger.info(f"Created patient: {patient.first_name} {patient.last_name} (MRN: {medical_record_number})")
            return patient
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating patient: {e}")
            raise
    
    def get_patient_by_id(self, db: Session, patient_id: int) -> Optional[Patient]:
        """Get patient by ID"""
        return db.query(Patient).filter(Patient.id == patient_id).first()
    
    def get_patient_by_phone(self, db: Session, phone_number: str) -> Optional[Patient]:
        """Get patient by phone number"""
        return db.query(Patient).filter(Patient.phone_number == phone_number).first()
    
    def get_patient_by_mrn(self, db: Session, mrn: str) -> Optional[Patient]:
        """Get patient by medical record number"""
        return db.query(Patient).filter(Patient.medical_record_number == mrn).first()
    
    def update_patient(
        self, 
        db: Session, 
        patient_id: int, 
        **updates
    ) -> Optional[Patient]:
        """Update patient information"""
        
        try:
            patient = self.get_patient_by_id(db, patient_id)
            if not patient:
                return None
            
            # Update fields
            for field, value in updates.items():
                if hasattr(patient, field):
                    setattr(patient, field, value)
            
            patient.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(patient)
            
            self.logger.info(f"Updated patient {patient_id}")
            return patient
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating patient {patient_id}: {e}")
            raise
    
    def get_patients_for_calls(
        self, 
        db: Session, 
        call_type: str,
        limit: int = 100
    ) -> List[Patient]:
        """Get patients who need calls of a specific type"""
        
        # This would implement business logic for determining
        # which patients need what type of calls based on their
        # surgery dates, previous calls, etc.
        
        return db.query(Patient).filter(
            Patient.is_active == True
        ).limit(limit).all()
    
    def get_patient_call_history(
        self, 
        db: Session, 
        patient_id: int
    ) -> List[CallSession]:
        """Get call history for a patient"""
        
        return db.query(CallSession).filter(
            CallSession.patient_id == patient_id
        ).order_by(CallSession.created_at.desc()).all()
    
    def deactivate_patient(self, db: Session, patient_id: int) -> bool:
        """Deactivate a patient (soft delete)"""
        
        try:
            patient = self.get_patient_by_id(db, patient_id)
            if not patient:
                return False
            
            patient.is_active = False
            patient.updated_at = datetime.utcnow()
            db.commit()
            
            self.logger.info(f"Deactivated patient {patient_id}")
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deactivating patient {patient_id}: {e}")
            return False
    
    def search_patients(
        self, 
        db: Session, 
        query: str, 
        limit: int = 50
    ) -> List[Patient]:
        """Search patients by name, phone, or MRN"""
        
        search_term = f"%{query}%"
        
        return db.query(Patient).filter(
            (Patient.first_name.ilike(search_term)) |
            (Patient.last_name.ilike(search_term)) |
            (Patient.phone_number.ilike(search_term)) |
            (Patient.medical_record_number.ilike(search_term))
        ).filter(Patient.is_active == True).limit(limit).all()
    
    def get_patient_statistics(self, db: Session) -> Dict[str, Any]:
        """Get patient statistics"""
        
        total_patients = db.query(Patient).filter(Patient.is_active == True).count()
        
        # Add more statistics as needed
        recent_patients = db.query(Patient).filter(
            Patient.created_at >= datetime.utcnow() - timedelta(days=30),
            Patient.is_active == True
        ).count()
        
        return {
            "total_active_patients": total_patients,
            "patients_added_last_30_days": recent_patients,
        }


# Factory function for dependency injection
_patient_service = None

def get_patient_service() -> PatientService:
    """Get or create PatientService instance (singleton pattern)"""
    global _patient_service
    if _patient_service is None:
        _patient_service = PatientService()
    return _patient_service 