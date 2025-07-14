"""
Conversation Manager Service
Orchestrates the conversation flow using call context and clinical rules.
Replaces the missing ConversationManager referenced in the system.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .call_context_service import CallContextService, CallContext
from .clinical_rules import ClinicalRulesService
from .speech_to_text import get_stt_service
from .voice_chat import get_chat_service
from models.patient import Patient
from models.call_session import CallSession

logger = logging.getLogger(__name__)


class ConversationFlow:
    """Base class for conversation flows"""
    
    def __init__(self, call_context: CallContext, clinical_rules: ClinicalRulesService):
        self.call_context = call_context
        self.clinical_rules = clinical_rules
        self.current_section = 0
        self.conversation_state = {
            'completed_sections': [],
            'collected_data': {},
            'escalations': [],
            'risk_assessments': []
        }
    
    def get_next_question(self) -> Optional[str]:
        """Get the next question based on current flow state"""
        raise NotImplementedError
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process patient response and determine next action"""
        raise NotImplementedError
    
    def should_escalate(self) -> bool:
        """Check if conversation should be escalated"""
        return len(self.conversation_state['escalations']) > 0


class ContextualConversationFlow(ConversationFlow):
    """Dynamic conversation flow based on call context"""
    
    def __init__(self, call_context: CallContext, clinical_rules: ClinicalRulesService):
        super().__init__(call_context, clinical_rules)
        self.sections = call_context.conversation_structure.get('sections', [])
        self.focus_areas = call_context.focus_areas
        
    def get_current_section(self) -> Optional[Dict[str, Any]]:
        """Get current conversation section"""
        if self.current_section < len(self.sections):
            section = self.sections[self.current_section]
            if hasattr(section, '__dict__'):
                return {
                    'name': section.name,
                    'purpose': section.purpose,
                    'key_questions': section.key_questions,
                    'required_data': section.required_data,
                    'escalation_criteria': section.escalation_criteria
                }
            return section
        return None
    
    def get_next_question(self) -> Optional[str]:
        """Get the next question based on current context"""
        current_section = self.get_current_section()
        if not current_section:
            return None
        
        # Get questions from current section
        questions = current_section.get('key_questions', [])
        
        # Find next unasked question
        asked_questions = self.conversation_state.get('asked_questions', [])
        for question in questions:
            if question not in asked_questions:
                return question
        
        # Move to next section if all questions answered
        self.current_section += 1
        return self.get_next_question()
    
    def process_response(self, user_response: str) -> Dict[str, Any]:
        """Process patient response with clinical assessment"""
        current_section = self.get_current_section()
        if not current_section:
            return {'status': 'completed', 'next_action': 'end_call'}
        
        # Store response
        section_name = current_section['name']
        if section_name not in self.conversation_state['collected_data']:
            self.conversation_state['collected_data'][section_name] = []
        
        self.conversation_state['collected_data'][section_name].append({
            'response': user_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Assess clinical risk if this is a medical response
        if self._is_medical_response(section_name):
            risk_assessment = self._assess_response_risk(user_response, section_name)
            if risk_assessment:
                self.conversation_state['risk_assessments'].append(risk_assessment)
                
                # Check for escalation triggers
                if risk_assessment.get('escalate', False):
                    self.conversation_state['escalations'].append({
                        'section': section_name,
                        'reason': risk_assessment.get('reason'),
                        'urgency': risk_assessment.get('urgency', 'moderate')
                    })
        
        return {
            'status': 'continue',
            'next_action': 'ask_next_question',
            'risk_level': self._calculate_current_risk(),
            'escalation_needed': self.should_escalate()
        }
    
    def _is_medical_response(self, section_name: str) -> bool:
        """Check if section requires medical assessment"""
        medical_sections = [
            'baseline_mobility_assessment',
            'medical_optimization_review',
            'pain_level_evaluation'
        ]
        return section_name in medical_sections
    
    def _assess_response_risk(self, response: str, section_name: str) -> Optional[Dict[str, Any]]:
        """Assess risk based on patient response"""
        response_lower = response.lower()
        
        # Pain level assessment
        if 'pain' in section_name and any(word in response_lower for word in ['8', '9', '10', 'severe', 'terrible', 'unbearable']):
            return {
                'risk_level': 'high',
                'reason': 'severe_pain_reported',
                'escalate': True,
                'urgency': 'high'
            }
        
        # Support system assessment
        if 'support' in section_name and any(word in response_lower for word in ['no one', 'alone', 'no help', 'nobody']):
            return {
                'risk_level': 'moderate',
                'reason': 'inadequate_support_system',
                'escalate': True,
                'urgency': 'moderate'
            }
        
        # Medical conditions assessment
        if 'medical' in section_name and any(word in response_lower for word in ['uncontrolled', 'high blood', 'diabetes', 'not taking']):
            return {
                'risk_level': 'moderate',
                'reason': 'medical_optimization_needed',
                'escalate': True,
                'urgency': 'moderate'
            }
        
        return None
    
    def _calculate_current_risk(self) -> str:
        """Calculate overall risk level from assessments"""
        risk_levels = [assessment.get('risk_level', 'low') for assessment in self.conversation_state['risk_assessments']]
        
        if 'high' in risk_levels:
            return 'high'
        elif 'moderate' in risk_levels:
            return 'moderate'
        else:
            return 'low'


class ConversationManager:
    """Main conversation manager orchestrating flows and services"""
    
    def __init__(self):
        self.call_context_service = CallContextService()
        self.clinical_rules_service = ClinicalRulesService()
        self.stt_service = get_stt_service()
        self.chat_service = get_chat_service()
        self.active_flows: Dict[str, ConversationFlow] = {}
        
    def start_conversation(self, patient: Patient, call_session: CallSession) -> Dict[str, Any]:
        """Start a new conversation flow"""
        try:
            # Generate call context
            call_context = self.call_context_service.get_call_context(patient, call_session)
            
            # Create appropriate flow
            flow = ContextualConversationFlow(call_context, self.clinical_rules_service)
            
            # Store active flow
            session_key = f"{patient.id}_{call_session.id}"
            self.active_flows[session_key] = flow
            
            # Generate initial message
            initial_message = self._generate_initial_message(call_context)
            
            return {
                'status': 'started',
                'initial_message': initial_message,
                'call_context': {
                    'call_type': call_context.call_type.value,
                    'days_from_surgery': call_context.days_from_surgery,
                    'focus_areas': call_context.focus_areas,
                    'tone': call_context.tone
                },
                'session_key': session_key
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def process_message(self, session_key: str, user_message: str) -> Dict[str, Any]:
        """Process user message and generate response"""
        try:
            if session_key not in self.active_flows:
                return {
                    'status': 'error',
                    'error': 'No active conversation found'
                }
            
            flow = self.active_flows[session_key]
            
            # Process the response
            result = flow.process_response(user_message)
            
            # Generate next response
            if result['status'] == 'continue':
                next_question = flow.get_next_question()
                
                return {
                    'status': 'continue',
                    'response': next_question,
                    'risk_level': result.get('risk_level', 'low'),
                    'escalation_needed': result.get('escalation_needed', False),
                    'conversation_state': flow.conversation_state
                }
            else:
                # Conversation completed
                return {
                    'status': 'completed',
                    'response': 'Thank you for your time. We have all the information we need for now.',
                    'final_state': flow.conversation_state
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_initial_message(self, call_context: CallContext) -> str:
        """Generate initial call message based on context"""
        patient_name = call_context.patient_data.get('name', 'Patient')
        call_type = call_context.call_type.value
        
        if call_type == 'enrollment':
            return f"Hello {patient_name}, this is your healthcare assistant calling about your upcoming knee replacement surgery. Is this a good time to talk?"
        elif call_type == 'education':
            week = call_context.conversation_structure.get('week', 'this week')
            focus = call_context.conversation_structure.get('focus_topic', 'your surgery preparation')
            return f"Hello {patient_name}, this is your healthcare assistant calling for your {week} education call about {focus}. How are you doing today?"
        else:
            return f"Hello {patient_name}, this is your healthcare assistant calling to check on your progress. How are you feeling today?"
    
    def get_flow_status(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get current flow status"""
        if session_key not in self.active_flows:
            return None
        
        flow = self.active_flows[session_key]
        return {
            'current_section': flow.current_section,
            'total_sections': len(flow.sections),
            'conversation_state': flow.conversation_state,
            'risk_level': flow._calculate_current_risk(),
            'escalation_needed': flow.should_escalate()
        }
    
    def end_conversation(self, session_key: str) -> Dict[str, Any]:
        """End conversation and clean up"""
        if session_key in self.active_flows:
            flow = self.active_flows[session_key]
            final_state = flow.conversation_state
            del self.active_flows[session_key]
            
            return {
                'status': 'ended',
                'final_state': final_state
            }
        
        return {'status': 'not_found'}


# Factory function for dependency injection
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Get or create ConversationManager instance (singleton pattern)"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
