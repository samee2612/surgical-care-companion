"""
Twilio Voice Service

Handles Twilio voice calls, speech-to-text streaming, and call orchestration.
Provides comprehensive features for initiating calls, managing conversation flow,
and processing audio streams for transcription.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import base64

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record, Stream
from twilio.base.exceptions import TwilioException
import httpx

from config import settings
from services.speech_to_text import SpeechToTextService

logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Call status enumeration"""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELED = "canceled"


class CallDirection(Enum):
    """Call direction enumeration"""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


@dataclass
class CallPayload:
    """Payload for initiating a call"""
    to_number: str
    patient_id: str
    call_session_id: str
    initial_message: str
    call_type: str
    context_data: Dict[str, Any]
    expected_duration_minutes: int = 15
    webhook_url: Optional[str] = None
    callback_url: Optional[str] = None


@dataclass
class AudioStreamData:
    """Audio stream data from Twilio"""
    call_sid: str
    sequence_number: int
    timestamp: str
    payload: str  # Base64 encoded audio
    track: str = "inbound"  # inbound/outbound


@dataclass
class TranscriptionResult:
    """Result from speech-to-text processing"""
    text: str
    confidence: float
    is_final: bool
    timestamp: datetime
    duration_ms: int


class TwilioVoiceService:
    """
    Comprehensive Twilio Voice Service
    
    Features:
    - Initiate outbound calls with custom payloads
    - Handle inbound call webhooks
    - Real-time audio streaming for transcription
    - Call flow management with TwiML generation
    - Integration with speech-to-text service
    - Call status tracking and callbacks
    """
    
    def __init__(self):
        """Initialize Twilio service with configuration"""
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN]):
            raise ValueError("Twilio credentials not configured")
        
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.webhook_base_url = settings.TWILIO_WEBHOOK_URL or "https://your-ngrok-url.com"
        
        # Initialize speech-to-text service
        self.stt_service = SpeechToTextService()
        
        # Active calls tracking
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
        # Registered callback handlers
        self.status_callbacks: List[Callable] = []
        self.transcription_callbacks: List[Callable] = []
        
        logger.info("Twilio Voice Service initialized")
    
    async def initiate_call(self, payload: CallPayload) -> Dict[str, Any]:
        """
        Initiate an outbound call with specified payload
        
        Args:
            payload: Call configuration and context data
            
        Returns:
            Dict containing call information and status
        """
        try:
            # Validate phone number format
            if not self._is_valid_phone_number(payload.to_number):
                raise ValueError(f"Invalid phone number format: {payload.to_number}")
            
            # Generate webhook URLs
            webhook_url = f"{self.webhook_base_url}/api/v1/twilio/voice-webhook/{payload.call_session_id}"
            status_callback_url = f"{self.webhook_base_url}/api/v1/twilio/status-callback/{payload.call_session_id}"
            
            # Create call through Twilio with embedded TwiML
            call = self.client.calls.create(
                to=payload.to_number,
                from_=self.phone_number,
                twiml=f'''<Response>
                    <Pause length="2"/>
                    <Say voice="alice">Hello! This is your surgical care companion calling to check on your recovery, Jane.</Say>
                    <Say voice="alice">How are you feeling today? I'll ask you a few quick questions about your recovery.</Say>
                    <Pause length="2"/>
                    <Say voice="alice">On a scale of 1 to 10, how would you rate your pain today?</Say>
                    <Pause length="3"/>
                    <Say voice="alice">How is your mobility? Are you able to walk and move around as instructed?</Say>
                    <Pause length="3"/>
                    <Say voice="alice">Are you taking your medications as prescribed?</Say>
                    <Pause length="3"/>
                    <Say voice="alice">Do you have any swelling, redness, or unusual symptoms at the surgery site?</Say>
                    <Pause length="3"/>
                    <Say voice="alice">Thank you for your time. Your responses help us monitor your recovery progress.</Say>
                    <Say voice="alice">Please remember to take your medications as prescribed, follow your physical therapy exercises, and contact your healthcare provider if you have any urgent concerns.</Say>
                    <Say voice="alice">We will continue to check on your progress. Take care and have a great day!</Say>
                    <Hangup/>
                </Response>''',
                timeout=30,
                machine_detection='Enable'  # Detect answering machines
            )
            
            # Store call context
            call_context = {
                'call_sid': call.sid,
                'patient_id': payload.patient_id,
                'call_session_id': payload.call_session_id,
                'initial_message': payload.initial_message,
                'call_type': payload.call_type,
                'context_data': payload.context_data,
                'status': CallStatus.INITIATED.value,
                'direction': CallDirection.OUTBOUND.value,
                'created_at': datetime.now(),
                'expected_duration_minutes': payload.expected_duration_minutes,
                'conversation_history': [],
                'transcripts': [],
                'current_step': 'greeting'
            }
            
            self.active_calls[call.sid] = call_context
            
            logger.info(f"Call initiated: {call.sid} to {payload.to_number}")
            
            return {
                'call_sid': call.sid,
                'status': call.status,
                'to': payload.to_number,
                'from': self.phone_number,
                'webhook_url': webhook_url,
                'created_at': call_context['created_at'].isoformat()
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error initiating call: {e}")
            raise Exception(f"Failed to initiate call: {e}")
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            raise
    
    def generate_greeting_twiml(self, call_session_id: str, initial_message: str) -> str:
        """
        Generate TwiML for initial call greeting
        
        Args:
            call_session_id: Session identifier
            initial_message: Initial message to speak
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        
        # Check if it's an answering machine
        response.pause(length=2)
        
        # Say initial greeting with a meaningful message
        greeting = initial_message or "Hello Jane! This is your surgical care companion calling to check on your recovery."
        response.say(greeting, voice='alice', language='en')
        
        # Ask how they're feeling
        response.say("How are you feeling today? Please tell me about your pain level, mobility, and any concerns you have.", voice='alice')
        
        # Record the patient's response
        response.record(
            action=f"{self.webhook_base_url}/api/v1/twilio/voice-webhook/{call_session_id}",
            method='POST',
            timeout=30,
            max_length=120,
            play_beep=True
        )
        
        # If no recording, provide some guidance
        response.say("I didn't receive your response. Please remember to take your medications as prescribed and follow your recovery plan.", voice='alice')
        response.say("If you have any urgent concerns, please contact your healthcare provider immediately.", voice='alice')
        response.say("Thank you for your time. Take care and continue following your recovery instructions.", voice='alice')
        response.hangup()
        
        return str(response)
    
    def generate_structured_questions_twiml(self, call_session_id: str, question_index: int = 0) -> str:
        """
        Generate TwiML for structured question flow
        
        Args:
            call_session_id: Session identifier
            question_index: Current question index
            
        Returns:
            TwiML XML string
        """
        # Get call context
        call_context = self.active_calls.get(call_session_id, {})
        questions = self._get_questions_for_call_type(call_context.get('call_type', 'followup'))
        
        response = VoiceResponse()
        
        if question_index < len(questions):
            question = questions[question_index]
            
            # Ask the question
            gather = Gather(
                input='speech',
                timeout=20,
                speech_timeout='auto',
                action=f"{self.webhook_base_url}/api/v1/twilio/process-answer/{call_session_id}/{question_index}",
                method='POST'
            )
            
            gather.say(question['text'], voice='alice')
            response.append(gather)
            
            # Fallback for no response
            response.say("I didn't hear your answer. Let me move to the next question.", voice='alice')
            response.redirect(f"{self.webhook_base_url}/api/v1/twilio/structured-questions/{call_session_id}/{question_index + 1}")
        else:
            # End of questions
            response.say("Thank you for your time. Take care and have a great day!", voice='alice')
            response.hangup()
        
        return str(response)
    
    async def process_audio_stream(self, call_sid: str, stream_data: AudioStreamData) -> Optional[TranscriptionResult]:
        """
        Process incoming audio stream for real-time transcription
        
        Args:
            call_sid: Twilio call SID
            stream_data: Audio stream data from Twilio
            
        Returns:
            Transcription result if available
        """
        try:
            # Decode audio payload
            audio_data = base64.b64decode(stream_data.payload)
            
            # Send to speech-to-text service
            transcription = await self.stt_service.transcribe_stream(
                audio_data=audio_data,
                session_id=call_sid,
                is_final=False  # Real-time streaming
            )
            
            if transcription and transcription.text.strip():
                # Store transcript
                if call_sid in self.active_calls:
                    self.active_calls[call_sid]['transcripts'].append({
                        'text': transcription.text,
                        'confidence': transcription.confidence,
                        'timestamp': transcription.timestamp.isoformat(),
                        'is_final': transcription.is_final,
                        'sequence': stream_data.sequence_number
                    })
                
                # Notify callbacks
                for callback in self.transcription_callbacks:
                    try:
                        await callback(call_sid, transcription)
                    except Exception as e:
                        logger.error(f"Error in transcription callback: {e}")
                
                return transcription
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return None
    
    async def process_speech_input(self, call_session_id: str, speech_result: str, confidence: float) -> str:
        """
        Process speech input and generate appropriate TwiML response
        
        Args:
            call_session_id: Session identifier
            speech_result: Transcribed speech text
            confidence: Confidence score
            
        Returns:
            TwiML response string
        """
        try:
            # Get call context
            call_context = self.active_calls.get(call_session_id, {})
            
            # Store the response
            response_data = {
                'text': speech_result,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'step': call_context.get('current_step', 'unknown')
            }
            
            if call_session_id in self.active_calls:
                self.active_calls[call_session_id]['conversation_history'].append(response_data)
            
            # Send to call service for processing
            await self._notify_call_service(call_session_id, speech_result, response_data)
            
            # Generate follow-up response
            response = VoiceResponse()
            
            # Determine next action based on context and response
            next_action = await self._determine_next_action(call_session_id, speech_result)
            
            if next_action['type'] == 'continue_conversation':
                response.say(next_action['message'], voice='alice')
                
                gather = Gather(
                    input='speech',
                    timeout=20,
                    speech_timeout='auto',
                    action=f"{self.webhook_base_url}/api/v1/twilio/process-speech/{call_session_id}",
                    method='POST'
                )
                gather.say(next_action['follow_up_question'], voice='alice')
                response.append(gather)
                
            elif next_action['type'] == 'structured_questions':
                response.redirect(f"{self.webhook_base_url}/api/v1/twilio/structured-questions/{call_session_id}")
                
            elif next_action['type'] == 'end_call':
                response.say(next_action['message'], voice='alice')
                response.hangup()
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error processing speech input: {e}")
            # Fallback response
            response = VoiceResponse()
            response.say("I'm having trouble processing your response. Let me ask you some specific questions.", voice='alice')
            response.redirect(f"{self.webhook_base_url}/api/v1/twilio/structured-questions/{call_session_id}")
            return str(response)
    
    async def handle_call_status_update(self, call_sid: str, status: str, **kwargs) -> None:
        """
        Handle call status updates from Twilio
        
        Args:
            call_sid: Twilio call SID
            status: New call status
            **kwargs: Additional status data
        """
        try:
            if call_sid in self.active_calls:
                self.active_calls[call_sid]['status'] = status
                self.active_calls[call_sid]['last_updated'] = datetime.now()
                
                # Add status-specific data
                if status == 'completed':
                    self.active_calls[call_sid]['completed_at'] = datetime.now()
                    self.active_calls[call_sid]['duration'] = kwargs.get('CallDuration', 0)
                
                # Notify callbacks
                for callback in self.status_callbacks:
                    try:
                        await callback(call_sid, status, kwargs)
                    except Exception as e:
                        logger.error(f"Error in status callback: {e}")
                
                logger.info(f"Call {call_sid} status updated to: {status}")
            
        except Exception as e:
            logger.error(f"Error handling call status update: {e}")
    
    def get_call_context(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get call context data"""
        return self.active_calls.get(call_sid)
    
    def get_call_transcripts(self, call_sid: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a call"""
        call_context = self.active_calls.get(call_sid, {})
        return call_context.get('transcripts', [])
    
    def get_conversation_history(self, call_sid: str) -> List[Dict[str, Any]]:
        """Get conversation history for a call"""
        call_context = self.active_calls.get(call_sid, {})
        return call_context.get('conversation_history', [])
    
    def register_status_callback(self, callback: Callable) -> None:
        """Register a callback for call status updates"""
        self.status_callbacks.append(callback)
    
    def register_transcription_callback(self, callback: Callable) -> None:
        """Register a callback for transcription updates"""
        self.transcription_callbacks.append(callback)
    
    def _is_valid_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        import re
        # Basic E.164 format validation
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))
    
    def _get_questions_for_call_type(self, call_type: str) -> List[Dict[str, Any]]:
        """Get structured questions based on call type"""
        questions_map = {
            'followup': [
                {'id': 'pain_level', 'text': 'On a scale of 1 to 10, what is your current pain level?'},
                {'id': 'mobility', 'text': 'How is your mobility today? Are you able to walk?'},
                {'id': 'wound_care', 'text': 'How does your surgical site look? Any redness, swelling, or discharge?'},
                {'id': 'medications', 'text': 'Are you taking your medications as prescribed?'},
                {'id': 'sleep', 'text': 'How well have you been sleeping?'},
                {'id': 'concerns', 'text': 'Do you have any concerns or questions about your recovery?'}
            ],
            'enrollment': [
                {'id': 'confirmation', 'text': 'Can you confirm your upcoming surgery date?'},
                {'id': 'transportation', 'text': 'Do you have transportation arranged for your surgery day?'},
                {'id': 'support_system', 'text': 'Who will be helping you during your recovery?'},
                {'id': 'home_prep', 'text': 'Have you prepared your home for recovery?'},
                {'id': 'medications_current', 'text': 'Are you currently taking any medications?'},
                {'id': 'concerns_pre', 'text': 'Do you have any concerns about the upcoming surgery?'}
            ],
            'education': [
                {'id': 'understanding', 'text': 'Do you understand the post-surgery care instructions?'},
                {'id': 'exercises', 'text': 'Are you doing your prescribed exercises?'},
                {'id': 'diet', 'text': 'How is your appetite and nutrition?'},
                {'id': 'activities', 'text': 'What activities are you currently able to do?'},
                {'id': 'goals', 'text': 'What are your recovery goals for this week?'}
            ]
        }
        
        return questions_map.get(call_type, questions_map['followup'])
    
    async def _determine_next_action(self, call_session_id: str, speech_result: str) -> Dict[str, Any]:
        """
        Determine next action based on speech input and context
        
        This could be enhanced with AI-powered decision making
        """
        # Simple rule-based logic for now
        # In production, this would integrate with the AI chat service
        
        if any(word in speech_result.lower() for word in ['emergency', 'urgent', 'severe', 'hospital']):
            return {
                'type': 'end_call',
                'message': 'I understand this may be urgent. A nurse will contact you shortly. Please call 911 if this is a medical emergency.'
            }
        
        if len(speech_result.split()) < 3:
            return {
                'type': 'structured_questions',
                'message': 'Let me ask you some specific questions to better understand how you\'re doing.'
            }
        
        return {
            'type': 'continue_conversation',
            'message': 'Thank you for sharing that information.',
            'follow_up_question': 'Is there anything else you\'d like to tell me about your recovery?'
        }
    
    async def _notify_call_service(self, call_session_id: str, speech_result: str, response_data: Dict[str, Any]) -> None:
        """
        Notify the call service about new speech input
        """
        try:
            # This would make an HTTP request to the call service
            # For now, we'll just log it
            logger.info(f"Speech input for session {call_session_id}: {speech_result}")
            
            # In production, make HTTP request to call service:
            # async with httpx.AsyncClient() as client:
            #     await client.post(
            #         f"{settings.BACKEND_URL}/api/v1/calls/{call_session_id}/speech-input",
            #         json=response_data
            #     )
            
        except Exception as e:
            logger.error(f"Error notifying call service: {e}")


# Global service instance
_twilio_service: Optional[TwilioVoiceService] = None


def get_twilio_service() -> TwilioVoiceService:
    """Get global Twilio service instance"""
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioVoiceService()
    return _twilio_service
