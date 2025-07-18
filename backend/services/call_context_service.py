"""
Call Context Service
Manages call contexts for different stages of patient care.
Provides context injection for AI conversations based on call type and patient data.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.models.patient import Patient
from backend.models.call_session import CallSession


class CallType(Enum):
    """Enum for different call types"""
    INITIAL_CLINICAL_ASSESSMENT = "initial_clinical_assessment"
    PREPARATION = "preparation"
    FINAL_PREP = "final_prep"
    FINAL_LOGISTICS = "final_logistics"


@dataclass
class CallContext:
    """Complete context for a patient call"""
    call_type: CallType
    days_from_surgery: int
    patient_data: Dict[str, Any]
    conversation_structure: Dict[str, Any]
    focus_areas: List[str]
    escalation_triggers: List[str]
    tone: str
    estimated_duration_minutes: int


@dataclass
class ConversationSection:
    """Individual section within a call"""
    name: str
    purpose: str
    key_questions: List[str]
    required_data: List[str]
    escalation_criteria: List[str]


class CallContextService:
    """Service for managing call contexts and conversation flows"""
    
    def __init__(self):
        self.call_definitions = self._initialize_call_definitions()
    
    def _initialize_call_definitions(self) -> Dict[CallType, Dict[str, Any]]:
        """Initialize call type definitions"""
        return {
            CallType.INITIAL_CLINICAL_ASSESSMENT: {
                "days_from_surgery": -35,  # 5 weeks pre-op (4-6 weeks range)
                "duration_minutes": 3,
                "primary_focus": "baseline_assessment",
                "secondary_focus": "information_collection",
                "tone": "efficient_caring",
                "sections": [
                    "surgery_confirmation",
                    "pain_assessment",
                    "activity_limitations",
                    "support_system"
                ],
                "escalation_triggers": [
                    "no_support_system",
                    "unsafe_home_environment",
                    "transportation_issues",
                    "uncontrolled_medical_conditions",
                    "high_anxiety_levels"
                ]
            },
            CallType.PREPARATION: {
                "days_from_surgery": -21,  # 3 weeks pre-op (2-3 weeks range)
                "duration_minutes": 5,
                "primary_focus": "home_safety_assessment",
                "secondary_focus": "medical_readiness",
                "tone": "supportive_practical",
                "sections": [
                    "home_safety_check",
                    "medical_preparation_status",
                    "equipment_availability",
                    "support_system_verification"
                ],
                "escalation_triggers": [
                    "unsafe_home_environment",
                    "missing_medical_clearances",
                    "equipment_not_available",
                    "inadequate_support_system",
                    "high_anxiety_about_preparation"
                ]
            }
        }
    
    def get_call_context(self, patient: Patient, call_session: CallSession) -> CallContext:
        """Generate complete call context for a patient call"""
        
        call_type = CallType(call_session.call_type)
        call_definition = self.call_definitions[call_type]
        
        # Build patient data context
        patient_data = self._build_patient_context(patient, call_session)
        
        # Build conversation structure
        days_from_surgery = getattr(call_session, "days_from_surgery", 0)
        conversation_structure = self._build_conversation_structure(call_type, days_from_surgery)
        
        return CallContext(
            call_type=call_type,
            days_from_surgery=days_from_surgery,
            patient_data=patient_data,
            conversation_structure=conversation_structure,
            focus_areas=call_definition["sections"],
            escalation_triggers=call_definition["escalation_triggers"],
            tone=call_definition["tone"],
            estimated_duration_minutes=call_definition["duration_minutes"]
        )
    
    def _build_patient_context(self, patient: Patient, call_session: CallSession) -> Dict[str, Any]:
        """Build patient-specific context data"""
        
        # Calculate surgery timing
        days_until_surgery = (patient.surgery_date - datetime.now()).days
        
        return {
            "patient_id": str(patient.id),
            "name": patient.name,
            "surgery_date": patient.surgery_date.isoformat(),
            "days_until_surgery": days_until_surgery,
            "days_from_surgery": call_session.days_from_surgery,
            "primary_phone": patient.primary_phone_number,
            "current_compliance_score": patient.overall_compliance_score,
            "readiness_status": patient.surgery_readiness_status,
            "physician_id": getattr(patient, "primary_physician_id", None),
            "physician": str(getattr(patient, "primary_physician_id", None)) if getattr(patient, "primary_physician_id", None) else "Unknown",
            "call_history": self._get_previous_call_summary(patient)
        }
    
    def _get_previous_call_summary(self, patient: Patient) -> List[Dict[str, Any]]:
        """Get summary of previous calls for context"""
        # For now, return empty list since Patient model doesn't have call_sessions relationship
        # In production, this would query the database for call sessions by patient_id
        return []
    
    def _build_conversation_structure(self, call_type: CallType, days_from_surgery: int) -> Dict[str, Any]:
        """Build the conversation flow structure for this call type"""
        
        if call_type == CallType.INITIAL_CLINICAL_ASSESSMENT:
            return self._build_initial_clinical_assessment_structure()
        elif call_type == CallType.PREPARATION:
            return self._build_preparation_structure()
        else:
            return {"sections": [], "flow": "standard"}
    
    def _build_initial_clinical_assessment_structure(self) -> Dict[str, Any]:
        print("FUCK OFF")
        """Build conversation structure for initial clinical assessment call (4-6 weeks pre-op)"""
        
        return {
            "call_purpose": "Comprehensive baseline assessment and information collection for upcoming surgery",
            "opening_approach": "warm_welcome_with_surgery_confirmation",
            "sections": [
                ConversationSection(
                    name="welcome_introduction",
                    purpose="Establish rapport and confirm surgery details",
                    key_questions=[
                        "Can you confirm your upcoming knee replacement surgery date?",
                        "How are you feeling about the upcoming procedure?",
                        "Do you have any immediate questions or concerns?"
                    ],
                    required_data=["surgery_confirmation", "initial_anxiety_level"],
                    escalation_criteria=["extreme_anxiety", "surgery_date_confusion"]
                ),
                ConversationSection(
                    name="baseline_mobility_assessment",
                    purpose="Establish current functional status",
                    key_questions=[
                        "How would you rate your current knee pain on a scale of 1-10?",
                        "What activities are most difficult for you right now?",
                        "Are you using any walking aids currently?",
                        "How far can you walk without significant pain?"
                    ],
                    required_data=["pain_level", "mobility_limitations", "current_aids", "walking_distance"],
                    escalation_criteria=["severe_disability", "concerning_symptoms"]
                ),
                
                ConversationSection(
                    name="support_system_mapping",
                    purpose="Identify available help and support",
                    key_questions=[
                        "Who will be helping you after surgery?",
                        "Will someone be staying with you the first few days?",
                        "Do you have family or friends who can assist with shopping or errands?",
                        "Are you comfortable asking for help when needed?"
                    ],
                    required_data=["primary_caregiver", "overnight_support", "errand_assistance", "comfort_asking_help"],
                    escalation_criteria=["no_support_system", "inadequate_immediate_help"]
                )
                
                
            ],
            "closing_approach": "summary_and_next_steps",
            "expected_outcomes": [
                "Baseline assessment completed",
                "Support system mapped",
                "Patient anxiety level assessed",
                "Next call scheduled and explained"
            ]
        }
    
    def _build_preparation_structure(self) -> Dict[str, Any]:
        """Build conversation structure for preparation call (2-3 weeks pre-op)"""
        
        return {
            "call_purpose": "Weekly preparation check-in focusing on home safety and medical readiness",
            "opening_approach": "warm_welcome_with_preparation_focus",
            "sections": [
                ConversationSection(
                    name="home_safety_assessment",
                    purpose="Evaluate home environment safety and remove trip hazards",
                    key_questions=[
                        "To prevent falls, it's important to remove trip hazards like loose rugs. Have you had a chance to prepare your recovery space?",
                        "Have you cleared pathways and removed any obstacles that could cause tripping?",
                        "Do you have good lighting in your main living areas and bathroom?",
                        "Are there any areas of your home that might be difficult to navigate after surgery?"
                    ],
                    required_data=["trip_hazards_removed", "pathways_cleared", "lighting_adequate", "navigation_challenges"],
                    escalation_criteria=["unsafe_environment", "trip_hazards_present", "poor_lighting", "accessibility_issues"]
                ),
                ConversationSection(
                    name="equipment_and_supplies",
                    purpose="Confirm availability of necessary equipment and supplies",
                    key_questions=[
                        "Have you obtained a raised toilet seat and a grabber tool? These are essential for following your hip precautions after surgery.",
                        "Do you have all the equipment you'll need for recovery?",
                        "Have you received your walker, crutches, or other mobility aids?",
                        "Do you have the necessary supplies for wound care?",
                        "Is there anything you're still waiting for?"
                    ],
                    required_data=["raised_toilet_seat", "grabber_tool", "equipment_available", "mobility_aids_received", "supplies_ready", "pending_items"],
                    escalation_criteria=["missing_equipment", "delayed_supplies", "inadequate_preparation"]
                ),
                ConversationSection(
                    name="medical_preparation_status",
                    purpose="Review medications and medical clearances",
                    key_questions=[
                        "Let's review medications. Are you currently taking any blood-thinning medication, such as Aspirin, Warfarin, or Eliquis?",
                        "Thank you. Your care team will give you specific instructions on when to stop.",
                        "Have you completed all your pre-surgery medical appointments?",
                        "Do you have all the required medical clearances?",
                        "Are there any pending medical tests or appointments?"
                    ],
                    required_data=["blood_thinning_medications", "appointments_completed", "clearances_obtained", "pending_tests", "medical_readiness"],
                    escalation_criteria=["missing_clearances", "incomplete_appointments", "medical_concerns", "blood_thinning_medications"]
                ),
                ConversationSection(
                    name="support_system_verification",
                    purpose="Confirm support system is ready and available",
                    key_questions=[
                        "Who will be helping you during your recovery?",
                        "Have you discussed your recovery needs with your support person?",
                        "Do you have backup support if your primary helper is unavailable?",
                        "Are you comfortable with your support arrangements?"
                    ],
                    required_data=["primary_caregiver", "support_discussed", "backup_support", "comfort_level"],
                    escalation_criteria=["no_support_system", "inadequate_support", "unprepared_caregiver"]
                )
            ],
            "closing_approach": "progress_summary_and_next_steps",
            "expected_outcomes": [
                "Home safety assessment completed",
                "Equipment and supplies confirmed",
                "Medical preparation status verified",
                "Support system verified",
                "Any gaps identified and addressed"
            ]
        }