"""
Call Orchestration Service

Orchestrates voice calls, manages conversation flow, and coordinates between
Twilio voice service, speech-to-text, and AI chat services for seamless
patient interaction.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.connection import get_db, SessionLocal
from models.patient import Patient
from models.call_session import CallSession
from services.twilio_service import TwilioVoiceService, CallPayload, get_twilio_service
from services.speech_to_text import get_stt_service
from services.voice_chat import get_chat_service
from services.call_context_service import CallContextService
from services.context_injection_service import ContextInjectionService
from services.notification_service import NotificationService
from config import settings

logger = logging.getLogger(__name__)


class CallPhase(Enum):
    """Call execution phases"""
    INITIATED = "initiated"
    GREETING = "greeting"
    CONVERSATION = "conversation"
    STRUCTURED_QUESTIONS = "structured_questions"
    SUMMARY = "summary"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CallResult:
    """Result from call execution"""
    call_session_id: str
    call_sid: Optional[str]
    status: str
    duration_seconds: int
    transcripts: List[Dict[str, Any]]
    conversation_summary: Dict[str, Any]
    clinical_alerts: List[Dict[str, Any]]
    next_call_scheduled: Optional[datetime]


class CallOrchestrationService:
    """
    Call Orchestration Service
    
    Main orchestrator for voice calls that:
    - Initiates calls through Twilio service
    - Manages conversation flow and context
    - Processes speech input through STT and AI services
    - Handles clinical decision making and alerts
    - Coordinates follow-up actions
    """
    
    def __init__(self):
        """Initialize call orchestration service"""
        self.twilio_service = get_twilio_service()
        self.stt_service = get_stt_service()
        self.chat_service = get_chat_service()
        self.context_service = CallContextService()
        self.injection_service = ContextInjectionService()
        self.notification_service = NotificationService()
        
        # Active call sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Register callbacks with Twilio service
        self.twilio_service.register_status_callback(self._handle_call_status_update)
        self.twilio_service.register_transcription_callback(self._handle_transcription_update)
        
        logger.info("Call Orchestration Service initialized")
    
    async def initiate_patient_call(
        self, 
        patient_id: str, 
        call_session_id: str,
        call_type: str = "followup"
    ) -> CallResult:
        """
        Initiate a call to a patient
        
        Args:
            patient_id: Patient identifier
            call_session_id: Call session identifier
            call_type: Type of call (followup, enrollment, education)
            
        Returns:
            CallResult with call execution details
        """
        try:
            # Get patient and call session from database
            db = SessionLocal()
            
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                db.close()
                raise ValueError(f"Patient not found: {patient_id}")
            
            call_session = db.query(CallSession).filter(CallSession.id == call_session_id).first()
            if not call_session:
                # Auto-create call session for testing purposes
                call_session = CallSession(
                    id=call_session_id,
                    patient_id=patient_id,
                    stage="postop",
                    surgery_type="knee",
                    scheduled_date=datetime.utcnow(),
                    days_from_surgery=1,
                    call_type=call_type,  # Use the provided call_type parameter
                    call_status="initiated"
                )
                db.add(call_session)
                db.commit()
                logger.info(f"Auto-created call session: {call_session_id}")
            
            # Refresh objects to ensure they're attached to session
            db.refresh(patient)
            db.refresh(call_session)
            
            # Keep references to the data we need
            patient_phone = patient.primary_phone_number
            patient_name = patient.name
            
            # Close the database session
            db.close()
            
            # Generate call context (using fresh objects)
            call_context = self.context_service.get_call_context(patient, call_session)
            
            # Generate initial conversation prompt
            prompt_data = self.injection_service.generate_llm_prompt(call_context, is_initial_call=True)
            
            # Create initial message for the call
            initial_message = await self._generate_initial_message(call_context, prompt_data)
            
            # Prepare call payload
            call_payload = CallPayload(
                to_number=patient_phone,
                patient_id=patient_id,
                call_session_id=call_session_id,
                initial_message=initial_message,
                call_type=call_type,
                context_data={
                    'call_context': call_context.__dict__,
                    'prompt_data': prompt_data,
                    'patient_name': patient_name
                },
                expected_duration_minutes=call_context.estimated_duration_minutes
            )
            
            # Store session context
            self.active_sessions[call_session_id] = {
                'patient_id': patient_id,
                'call_context': call_context,
                'prompt_data': prompt_data,
                'phase': CallPhase.INITIATED,
                'conversation_history': [],
                'transcripts': [],
                'clinical_data': {},
                'started_at': datetime.now(),
                'ai_responses': []
            }
            
            # Initiate call through Twilio
            call_info = await self.twilio_service.initiate_call(call_payload)
            
            # Update session with call info
            self.active_sessions[call_session_id].update({
                'call_sid': call_info['call_sid'],
                'twilio_status': call_info['status']
            })
            
            # Update database
            db_session = SessionLocal()
            try:
                db_session.query(CallSession).filter(CallSession.id == call_session_id).update({
                    'call_status': 'initiated',
                    'actual_call_start': datetime.now()
                })
                db_session.commit()
            finally:
                db_session.close()
            
            logger.info(f"Call initiated for patient {patient_id}, session {call_session_id}")
            
            return CallResult(
                call_session_id=call_session_id,
                call_sid=call_info['call_sid'],
                status='initiated',
                duration_seconds=0,
                transcripts=[],
                conversation_summary={},
                clinical_alerts=[],
                next_call_scheduled=None
            )
            
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            
            # Update session status
            if call_session_id in self.active_sessions:
                self.active_sessions[call_session_id]['phase'] = CallPhase.FAILED
                self.active_sessions[call_session_id]['error'] = str(e)
            
            raise
    
    async def process_speech_input(
        self, 
        call_session_id: str, 
        speech_text: str, 
        confidence: float
    ) -> Dict[str, Any]:
        """
        Process speech input from patient during call
        
        Args:
            call_session_id: Call session identifier
            speech_text: Transcribed speech text
            confidence: Transcription confidence score
            
        Returns:
            Processing result with next action
        """
        try:
            if call_session_id not in self.active_sessions:
                logger.error(f"No active session found for {call_session_id}")
                return {'error': 'Session not found'}
            
            session = self.active_sessions[call_session_id]
            
            # Store transcript
            transcript_entry = {
                'text': speech_text,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'phase': session['phase'].value
            }
            session['transcripts'].append(transcript_entry)
            
            # Update conversation phase
            if session['phase'] == CallPhase.INITIATED:
                session['phase'] = CallPhase.GREETING
            elif session['phase'] == CallPhase.GREETING:
                session['phase'] = CallPhase.CONVERSATION
            
            # Generate AI response using chat service
            ai_response = await self._generate_ai_response(session, speech_text)
            
            # Store AI response
            ai_entry = {
                'response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'input_text': speech_text,
                'phase': session['phase'].value
            }
            session['ai_responses'].append(ai_entry)
            
            # Extract clinical information
            clinical_data = await self._extract_clinical_data(speech_text, session)
            if clinical_data:
                session['clinical_data'].update(clinical_data)
            
            # Determine next action
            next_action = await self._determine_next_action(session, speech_text, ai_response)
            
            # Check for clinical alerts
            alerts = await self._check_clinical_alerts(session)
            if alerts:
                await self._handle_clinical_alerts(call_session_id, alerts)
            
            return {
                'ai_response': ai_response,
                'next_action': next_action,
                'clinical_data': clinical_data,
                'alerts': alerts,
                'session_phase': session['phase'].value
            }
            
        except Exception as e:
            logger.error(f"Error processing speech input: {e}")
            return {'error': str(e)}
    
    async def complete_call(self, call_session_id: str) -> CallResult:
        """
        Complete a call session and generate summary
        
        Args:
            call_session_id: Call session identifier
            
        Returns:
            CallResult with complete call details
        """
        try:
            if call_session_id not in self.active_sessions:
                raise ValueError(f"Session not found: {call_session_id}")
            
            session = self.active_sessions[call_session_id]
            session['phase'] = CallPhase.COMPLETED
            session['completed_at'] = datetime.now()
            
            # Calculate duration
            duration = (session['completed_at'] - session['started_at']).total_seconds()
            
            # Generate conversation summary
            conversation_summary = await self._generate_conversation_summary(session)
            
            # Generate clinical summary
            clinical_summary = await self._generate_clinical_summary(session)
            
            # Schedule next call if needed
            next_call_date = await self._schedule_next_call(session)
            
            # Update database
            with get_db() as db:
                db.query(CallSession).filter(CallSession.id == call_session_id).update({
                    'call_status': 'completed',
                    'actual_call_end': session['completed_at'],
                    'duration_seconds': int(duration),
                    'conversation_summary': json.dumps(conversation_summary),
                    'clinical_data': json.dumps(session['clinical_data'])
                })
                db.commit()
            
            # Clean up session
            result = CallResult(
                call_session_id=call_session_id,
                call_sid=session.get('call_sid'),
                status='completed',
                duration_seconds=int(duration),
                transcripts=session['transcripts'],
                conversation_summary=conversation_summary,
                clinical_alerts=session.get('alerts', []),
                next_call_scheduled=next_call_date
            )
            
            del self.active_sessions[call_session_id]
            
            logger.info(f"Call completed for session {call_session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error completing call: {e}")
            raise
    
    async def _generate_initial_message(self, call_context, prompt_data: Dict[str, Any]) -> str:
        """Generate initial greeting message for the call"""
        try:
            # Use AI service to generate personalized greeting
            initial_response = await self.chat_service.start_contextual_conversation(
                system_prompt=prompt_data["system_prompt"],
                user_prompt=prompt_data["user_prompt"],
                context_metadata=prompt_data["context_metadata"]
            )
            
            return initial_response
            
        except Exception as e:
            logger.error(f"Error generating initial message: {e}")
            # Fallback to generic greeting
            return f"Hello! This is your automated follow-up call. I'm calling to check on your recovery. How are you feeling today?"
    
    async def _generate_ai_response(self, session: Dict[str, Any], speech_text: str) -> str:
        """Generate AI response to patient speech"""
        try:
            # Build conversation history
            conversation_history = [
                {
                    'role': 'user' if i % 2 == 0 else 'assistant',
                    'content': entry.get('input_text' if i % 2 == 0 else 'response', '')
                }
                for i, entry in enumerate(session['ai_responses'])
            ]
            
            # Add current input
            conversation_history.append({
                'role': 'user',
                'content': speech_text
            })
            
            # Generate response using chat service
            response = await self.chat_service.generate_contextual_response(
                user_message=speech_text,
                system_prompt=session['prompt_data']['system_prompt'],
                context_metadata=session['prompt_data']['context_metadata'],
                conversation_history=conversation_history
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I understand. Can you tell me more about that?"
    
    async def _extract_clinical_data(self, speech_text: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clinical information from speech"""
        # This would integrate with NLU service or use AI to extract structured data
        # For now, simple keyword matching
        clinical_data = {}
        
        # Pain level extraction
        import re
        pain_match = re.search(r'pain.*?(\d+)', speech_text.lower())
        if pain_match:
            clinical_data['pain_level'] = int(pain_match.group(1))
        
        # Mobility keywords
        mobility_keywords = ['walk', 'walking', 'move', 'moving', 'mobility', 'exercise']
        if any(word in speech_text.lower() for word in mobility_keywords):
            clinical_data['mobility_mentioned'] = True
        
        # Concern keywords
        concern_keywords = ['concern', 'worried', 'problem', 'issue', 'trouble']
        if any(word in speech_text.lower() for word in concern_keywords):
            clinical_data['concerns_mentioned'] = True
        
        return clinical_data
    
    async def _determine_next_action(self, session: Dict[str, Any], speech_text: str, ai_response: str) -> Dict[str, Any]:
        """Determine next action in the conversation"""
        # Simple logic - in production this would be more sophisticated
        if session['phase'] == CallPhase.CONVERSATION:
            if len(session['ai_responses']) >= 5:  # Limit conversation length
                return {
                    'type': 'structured_questions',
                    'message': 'Let me ask you some specific questions about your recovery.'
                }
            else:
                return {
                    'type': 'continue_conversation',
                    'message': ai_response
                }
        
        return {
            'type': 'continue',
            'message': ai_response
        }
    
    async def _check_clinical_alerts(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for clinical alerts based on conversation data"""
        alerts = []
        clinical_data = session.get('clinical_data', {})
        
        # High pain level alert
        if clinical_data.get('pain_level', 0) >= settings.URGENT_ALERT_THRESHOLD:
            alerts.append({
                'type': 'high_pain_level',
                'severity': 'urgent',
                'value': clinical_data['pain_level'],
                'message': f"Patient reported pain level {clinical_data['pain_level']}"
            })
        
        # Concerns mentioned
        if clinical_data.get('concerns_mentioned'):
            alerts.append({
                'type': 'patient_concerns',
                'severity': 'moderate',
                'message': "Patient mentioned concerns during call"
            })
        
        return alerts
    
    async def _handle_clinical_alerts(self, call_session_id: str, alerts: List[Dict[str, Any]]) -> None:
        """Handle clinical alerts by notifying appropriate staff"""
        try:
            for alert in alerts:
                await self.notification_service.send_clinical_alert(
                    call_session_id=call_session_id,
                    alert_type=alert['type'],
                    severity=alert['severity'],
                    message=alert['message'],
                    data=alert
                )
                
                logger.info(f"Clinical alert sent for session {call_session_id}: {alert['type']}")
                
        except Exception as e:
            logger.error(f"Error handling clinical alerts: {e}")
    
    async def _generate_conversation_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of the conversation"""
        return {
            'total_responses': len(session['ai_responses']),
            'duration_minutes': (session['completed_at'] - session['started_at']).total_seconds() / 60,
            'phases_completed': [phase.value for phase in [CallPhase.GREETING, CallPhase.CONVERSATION]],
            'transcript_count': len(session['transcripts']),
            'clinical_data_points': len(session.get('clinical_data', {}))
        }
    
    async def _generate_clinical_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clinical summary from conversation"""
        # This would use AI to analyze the full conversation
        # For now, return structured clinical data
        return session.get('clinical_data', {})
    
    async def _schedule_next_call(self, session: Dict[str, Any]) -> Optional[datetime]:
        """Schedule next follow-up call if needed"""
        # Simple scheduling logic
        call_context = session['call_context']
        if call_context.call_type.value == 'followup':
            # Schedule next call in 3 days
            return datetime.now() + timedelta(days=3)
        
        return None
    
    async def _handle_call_status_update(self, call_sid: str, status: str, data: Dict[str, Any]) -> None:
        """Handle call status updates from Twilio"""
        # Find session by call_sid
        session_id = None
        for sid, session in self.active_sessions.items():
            if session.get('call_sid') == call_sid:
                session_id = sid
                break
        
        if session_id:
            self.active_sessions[session_id]['twilio_status'] = status
            logger.info(f"Call status updated for session {session_id}: {status}")
            
            if status == 'completed':
                await self.complete_call(session_id)
    
    async def _handle_transcription_update(self, call_sid: str, transcription) -> None:
        """Handle real-time transcription updates"""
        # Find session by call_sid
        session_id = None
        for sid, session in self.active_sessions.items():
            if session.get('call_sid') == call_sid:
                session_id = sid
                break
        
        if session_id and transcription.is_final:
            await self.process_speech_input(
                session_id, 
                transcription.text, 
                transcription.confidence
            )


# Global service instance
_call_service: Optional[CallOrchestrationService] = None


def get_call_service() -> CallOrchestrationService:
    """Get global call orchestration service instance"""
    global _call_service
    if _call_service is None:
        _call_service = CallOrchestrationService()
    return _call_service 