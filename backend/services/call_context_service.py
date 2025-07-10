"""
Call Context Service
Manages call contexts for different stages of patient care.
Provides context injection for AI conversations based on call type and patient data.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from models.patient import Patient
from models.call_session import CallSession


class CallType(Enum):
    """Enum for different call types"""
    ENROLLMENT = "enrollment"
    EDUCATION = "education"
    PREPARATION = "preparation"
    FINAL_PREP = "final_prep"


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
            CallType.ENROLLMENT: {
                "days_from_surgery": -42,
                "duration_minutes": 20,
                "primary_focus": "baseline_assessment",
                "secondary_focus": "information_collection",
                "tone": "comprehensive_welcoming",
                "sections": [
                    "welcome_introduction",
                    "surgery_confirmation",
                    "baseline_mobility_assessment",
                    "pain_level_evaluation",
                    "home_environment_assessment",
                    "support_system_mapping",
                    "medical_optimization_review",
                    "transportation_planning",
                    "next_steps_overview"
                ],
                "escalation_triggers": [
                    "no_support_system",
                    "unsafe_home_environment",
                    "transportation_issues",
                    "uncontrolled_medical_conditions",
                    "high_anxiety_levels"
                ]
            },
            CallType.EDUCATION: {
                "days_from_surgery": [-28, -21, -14, -7],
                "duration_minutes": 15,
                "primary_focus": "knowledge_transfer",
                "secondary_focus": "progress_tracking",
                "tone": "educational_encouraging",
                "sections": [
                    "progress_check",
                    "education_delivery",
                    "exercise_review",
                    "preparation_guidance",
                    "question_resolution"
                ],
                "escalation_triggers": [
                    "concerning_symptoms",
                    "non_compliance",
                    "equipment_delays"
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
        conversation_structure = self._build_conversation_structure(call_type, call_session.days_from_surgery)
        
        return CallContext(
            call_type=call_type,
            days_from_surgery=call_session.days_from_surgery,
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
            "physician": patient.primary_physician.name if patient.primary_physician else "Unknown",
            "call_history": self._get_previous_call_summary(patient)
        }
    
    def _get_previous_call_summary(self, patient: Patient) -> List[Dict[str, Any]]:
        """Get summary of previous calls for context"""
        previous_calls = []
        
        for call in patient.call_sessions:
            if call.call_status == "completed":
                previous_calls.append({
                    "call_type": call.call_type,
                    "date": call.actual_call_start.isoformat() if call.actual_call_start else None,
                    "outcome": call.call_outcome,
                    "compliance_score": call.compliance_score,
                    "concerns": call.concerns_identified or []
                })
        
        return sorted(previous_calls, key=lambda x: x["date"] or "", reverse=True)
    
    def _build_conversation_structure(self, call_type: CallType, days_from_surgery: int) -> Dict[str, Any]:
        """Build the conversation flow structure for this call type"""
        
        if call_type == CallType.ENROLLMENT:
            return self._build_enrollment_structure()
        elif call_type == CallType.EDUCATION:
            return self._build_education_structure(days_from_surgery)
        else:
            return {"sections": [], "flow": "standard"}
    
    def _build_enrollment_structure(self) -> Dict[str, Any]:
        """Build conversation structure for enrollment call (-42 days)"""
        
        return {
            "call_purpose": "Comprehensive baseline assessment and information collection",
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
                    name="home_environment_assessment",
                    purpose="Evaluate post-surgery safety and preparation needs",
                    key_questions=[
                        "Do you live in a single-story home or multi-story?",
                        "Are there stairs to enter your home?",
                        "Where is your bedroom located?",
                        "Do you have any trip hazards like loose rugs or clutter?",
                        "Is your bathroom easily accessible?"
                    ],
                    required_data=["home_layout", "stairs_present", "bedroom_location", "safety_hazards", "bathroom_access"],
                    escalation_criteria=["unsafe_environment", "major_accessibility_issues"]
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
                ),
                ConversationSection(
                    name="medical_optimization_review",
                    purpose="Ensure medical conditions are well-controlled",
                    key_questions=[
                        "Do you have diabetes, high blood pressure, or heart conditions?",
                        "Are you taking any blood thinners?",
                        "When was your last physical exam?",
                        "Are all your chronic conditions well-controlled?",
                        "Do you need any medical clearances?"
                    ],
                    required_data=["chronic_conditions", "medications", "recent_exam", "condition_control", "clearances_needed"],
                    escalation_criteria=["uncontrolled_conditions", "medication_concerns", "missing_clearances"]
                ),
                ConversationSection(
                    name="transportation_planning",
                    purpose="Ensure safe transportation arrangements",
                    key_questions=[
                        "How will you get to the hospital for surgery?",
                        "Who will drive you home after surgery?",
                        "Do you have transportation for follow-up appointments?",
                        "Are there any transportation challenges we should know about?"
                    ],
                    required_data=["surgery_transport", "discharge_transport", "followup_transport", "transport_challenges"],
                    escalation_criteria=["no_transport_plan", "unreliable_arrangements"]
                )
            ],
            "closing_approach": "summary_and_next_steps",
            "expected_outcomes": [
                "Baseline assessment completed",
                "Support system mapped",
                "Home safety evaluation done",
                "Medical optimization status known",
                "Transportation plan confirmed",
                "Patient anxiety level assessed",
                "Next call scheduled and explained"
            ]
        }
    
    def _build_education_structure(self, days_from_surgery: int) -> Dict[str, Any]:
        """Build conversation structure for education calls"""
        
        # Determine which week based on days from surgery
        if days_from_surgery == -28:
            return self._build_week4_education()  # Surgery overview
        elif days_from_surgery == -21:
            return self._build_week3_education()  # Home preparation
        elif days_from_surgery == -14:
            return self._build_week2_education()  # Pain management
        elif days_from_surgery == -7:
            return self._build_week1_education()  # Hospital stay
        else:
            return {
                "call_purpose": f"Educational call at {days_from_surgery} days from surgery",
                "sections": [],
                "expected_outcomes": []
            }
    
    def _build_week4_education(self) -> Dict[str, Any]:
        """Week 4: Surgery overview and recovery expectations"""
        return {
            "call_purpose": "Surgery overview and recovery expectations education",
            "week": "Week 4",
            "focus_topic": "Surgery Overview and Recovery Expectations",
            "tone": "informative_reassuring",
            "sections": [
                "check_in_since_enrollment",
                "surgery_procedure_overview", 
                "recovery_timeline_expectations",
                "address_surgery_concerns",
                "next_week_preview"
            ],
            "expected_outcomes": [
                "Patient understands surgery procedure",
                "Recovery timeline clarified",
                "Surgery anxieties addressed",
                "Confidence in surgical decision increased"
            ]
        }
    
    def _build_week3_education(self) -> Dict[str, Any]:
        """Week 3: Home preparation requirements"""
        return {
            "call_purpose": "Home preparation requirements education",
            "week": "Week 3", 
            "focus_topic": "Home Preparation Requirements",
            "tone": "practical_helpful",
            "sections": [
                "progress_check_from_week4",
                "home_safety_modifications",
                "equipment_and_supplies_needed",
                "accessibility_planning",
                "preparation_timeline"
            ],
            "expected_outcomes": [
                "Home safety plan created",
                "Equipment list provided",
                "Modification timeline established",
                "Patient confident about home setup"
            ]
        }
    
    def _build_week2_education(self) -> Dict[str, Any]:
        """Week 2: Pain management planning"""
        return {
            "call_purpose": "Pain management planning education",
            "week": "Week 2",
            "focus_topic": "Pain Management Planning", 
            "tone": "educational_supportive",
            "sections": [
                "home_preparation_progress_check",
                "pain_management_overview",
                "medication_planning",
                "non_medication_strategies",
                "pain_expectations_timeline"
            ],
            "expected_outcomes": [
                "Pain management plan understood",
                "Medication schedule clarified",
                "Non-drug strategies learned",
                "Realistic pain expectations set"
            ]
        }
    
    def _build_week1_education(self) -> Dict[str, Any]:
        """Week 1: Hospital stay and immediate post-op period"""
        return {
            "call_purpose": "Hospital stay and immediate post-op education",
            "week": "Week 1",
            "focus_topic": "Hospital Stay and Immediate Post-Op Period",
            "tone": "reassuring_detailed",
            "sections": [
                "final_preparation_check",
                "hospital_admission_process",
                "surgery_day_timeline",
                "immediate_post_op_expectations",
                "discharge_planning_overview"
            ],
            "expected_outcomes": [
                "Hospital process understood",
                "Surgery day timeline clear",
                "Post-op expectations realistic",
                "Discharge plan confirmed"
            ]
        } 