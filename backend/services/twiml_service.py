"""
Twilio TwiML Service - Interactive Voice Response System
Handles interactive voice conversations with patients for post-surgical care monitoring
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json

from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.orm import Session

from models import Patient, VoiceInteraction, Surgery

# Backward compatibility
Conversation = VoiceInteraction
from services.gemini_service import gemini_service
from services.transcription_service import transcription_service

logger = logging.getLogger(__name__)

class CallState(Enum):
    """Enum for call states"""
    GREETING = "greeting"
    INITIAL_ASSESSMENT = "initial_assessment"
    PAIN_ASSESSMENT = "pain_assessment"
    WOUND_CHECK = "wound_check"
    MEDICATION_CHECK = "medication_check"
    FOLLOW_UP = "follow_up"
    COMPLETION = "completion"
    ERROR = "error"

class ConversationFlow:
    """Manages conversation flow and question progression"""
    
    def __init__(self):
        self.question_flows = {
            CallState.GREETING: [
                "Hello! This is your surgical care companion calling to check on your recovery. How are you feeling today?",
                "I'm here to help monitor your post-surgical recovery. Let's start with a few questions about how you're doing."
            ],
            CallState.INITIAL_ASSESSMENT: [
                "Can you tell me about your overall recovery progress since your surgery?",
                "How would you describe your energy level and mobility today?",
                "Are you experiencing any unexpected symptoms or concerns?"
            ],
            CallState.PAIN_ASSESSMENT: [
                "On a scale of 1 to 10, with 10 being the worst pain imaginable, how would you rate your current pain level?",
                "Tell me about any pain you're experiencing. Where is it located and how would you describe it?",
                "Has your pain level changed since yesterday? Is it getting better, worse, or staying the same?"
            ],
            CallState.WOUND_CHECK: [
                "How does your surgical site look today? Are you noticing any changes?",
                "Have you seen any redness, swelling, or unusual discharge around your incision?",
                "Are you following the wound care instructions your doctor gave you?"
            ],
            CallState.MEDICATION_CHECK: [
                "Are you taking all your prescribed medications as directed?",
                "Are you experiencing any side effects from your medications?",
                "Do you have any questions about your medication schedule or dosages?"
            ],
            CallState.FOLLOW_UP: [
                "Is there anything else about your recovery that you'd like to discuss?",
                "Do you have any questions or concerns that we haven't covered?",
                "Are you following up with your doctor as scheduled?"
            ]
        }
    
    def get_next_question(self, current_state: CallState, conversation_history: List[Dict]) -> Optional[str]:
        """Get the next appropriate question based on current state and history"""
        try:
            # Check if we've covered enough topics
            if len(conversation_history) >= 10:
                return None  # End conversation
            
            # Get questions for current state
            questions = self.question_flows.get(current_state, [])
            if not questions:
                return None
            
            # Simple rotation through questions (can be made more intelligent)
            question_index = len([msg for msg in conversation_history if msg.get('role') == 'assistant']) % len(questions)
            return questions[question_index]
            
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return "Can you tell me more about how you're feeling today?"

class TwiMLService:
    """
    Main TwiML service for handling interactive voice conversations
    """
    
    def __init__(self):
        self.conversation_flow = ConversationFlow()
        self.speech_timeout = int(os.getenv("TWILIO_SPEECH_TIMEOUT", "5"))
        self.max_speech_time = int(os.getenv("TWILIO_MAX_SPEECH_TIME", "30"))
        self.language = os.getenv("TWILIO_LANGUAGE", "en-US")
        
        logger.info(f"TwiMLService initialized with timeout={self.speech_timeout}s, max_time={self.max_speech_time}s")
    
    async def handle_incoming_call(self, call_sid: str, from_number: str, patient: Patient, db: Session) -> str:
        """
        Handle incoming call and create initial conversation
        
        Args:
            call_sid: Twilio call SID
            from_number: Caller's phone number
            patient: Patient record
            db: Database session
            
        Returns:
            TwiML response string
        """
        try:
            logger.info(f"Handling incoming call: {call_sid} from {from_number}")
            
            # Get patient's most recent surgery for context
            surgery = db.query(Surgery).filter(Surgery.patient_id == patient.id).order_by(Surgery.surgery_date.desc()).first()
            if not surgery:
                logger.info(f"No surgery found for patient {patient.id}, creating default record")
                # Create a default surgery record if none exists
                surgery = Surgery(
                    patient_id=patient.id,
                    procedure="General Follow-up",
                    surgeon_name="Unknown",
                    surgery_date=datetime.utcnow().date(),
                    specialty="general"
                )
                db.add(surgery)
                db.commit()
                db.refresh(surgery)
            
            # Create conversation record
            conversation = Conversation(
                patient_id=patient.id,
                surgery_id=surgery.id,
                call_sid=call_sid,
                phone_number=from_number,
                call_direction="inbound",
                call_status="in-progress",
                call_date=datetime.utcnow(),
                conversation_json={"messages": [], "state": CallState.GREETING.value},
                started_at=datetime.utcnow()
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # Generate greeting - use simple greeting to avoid timeout
            greeting_msg = f"Hello {patient.first_name}! This is your surgical care companion. I'm calling to check on your recovery. How are you feeling today?"
            
            # Update conversation
            conversation.conversation_json["messages"].append({
                "role": "assistant",
                "content": greeting_msg,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "greeting",
                "state": CallState.GREETING.value
            })
            db.commit()
            
            # Create TwiML response with timeout protection
            response = VoiceResponse()
            
            gather = Gather(
                input="speech dtmf",
                timeout=10,
                action="/api/webhooks/twilio/voice",
                method="POST",
                speech_timeout=3,
                language="en-US",
                num_digits=1
            )
            
            gather.say(greeting_msg)
            response.append(gather)
            
            # Fallback if no input detected
            response.say("I didn't hear anything. Please try again or press 0 to end the call.")
            response.hangup()
            
            logger.info(f"Generated TwiML response for call {call_sid}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling incoming call {call_sid}: {e}")
            # Return simple error response to avoid further issues
            response = VoiceResponse()
            response.say("I'm sorry, there was an issue starting our conversation. Please try calling again.")
            response.hangup()
            return str(response)
    
    async def handle_speech_input(self, call_sid: str, form_data: dict, db: Session) -> str:
        """
        Handle speech input from user
        
        Args:
            call_sid: Twilio call SID
            form_data: Twilio webhook form data
            db: Database session
            
        Returns:
            TwiML response string
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Handling speech input for call {call_sid}")
            
            # Get conversation with error handling
            conversation = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
            if not conversation:
                logger.error(f"Conversation not found for call {call_sid}")
                return self._create_error_response("Conversation not found. Please try calling again.")
            
            # Extract speech with timeout protection
            try:
                speech_result = await asyncio.wait_for(
                    transcription_service.extract_speech_from_webhook(form_data),
                    timeout=5.0  # 5 second timeout
                )
                transcript = speech_result.get("text", "").strip()
                confidence = speech_result.get("confidence", 0)
            except asyncio.TimeoutError:
                logger.error(f"Speech extraction timeout for call {call_sid}")
                return self._handle_no_speech_detected(conversation, db)
            except Exception as speech_error:
                logger.error(f"Speech extraction error: {speech_error}")
                return self._handle_no_speech_detected(conversation, db)
            
            if not transcript:
                logger.info(f"No speech detected for call {call_sid}")
                return self._handle_no_speech_detected(conversation, db)
            
            logger.info(f"Speech detected: '{transcript}' (confidence: {confidence}) for call {call_sid}")
            
            # Add user message to conversation
            try:
                if not conversation.conversation_json:
                    conversation.conversation_json = {"messages": [], "state": CallState.GREETING.value}
                
                conversation.conversation_json["messages"].append({
                    "role": "user",
                    "content": transcript,
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": confidence,
                    "source": "speech"
                })
                db.commit()
            except Exception as conv_error:
                logger.error(f"Conversation update error: {conv_error}")
                # Continue without failing
            
            # Analyze with Gemini with timeout protection
            try:
                analysis = await asyncio.wait_for(
                    gemini_service.analyze_conversation(
                        transcript,
                        conversation.conversation_json.get("messages", [])
                    ),
                    timeout=8.0  # 8 second timeout for AI analysis
                )
                logger.info(f"Analysis completed for call {call_sid}")
            except asyncio.TimeoutError:
                logger.error(f"Gemini analysis timeout for call {call_sid}")
                # Use fallback analysis
                analysis = {
                    "intent": "general_inquiry",
                    "urgency_level": "low",
                    "requires_immediate_attention": False,
                    "entities": {},
                    "sentiment": "neutral",
                    "recommended_actions": []
                }
            except Exception as analysis_error:
                logger.error(f"Gemini analysis error: {analysis_error}")
                # Use fallback analysis
                analysis = {
                    "intent": "general_inquiry",
                    "urgency_level": "low",
                    "requires_immediate_attention": False,
                    "entities": {},
                    "sentiment": "neutral",
                    "recommended_actions": []
                }
            
            # Update conversation with analysis
            try:
                self._update_conversation_with_analysis(conversation, analysis)
                db.commit()
            except Exception as update_error:
                logger.error(f"Analysis update error: {update_error}")
                # Continue without failing
            
            # Determine next action
            next_response = await self._determine_next_action(conversation, analysis, db)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Speech input handled successfully in {duration:.2f}s for call {call_sid}")
            
            return next_response
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error handling speech input for call {call_sid}: {e} (duration: {duration:.2f}s)")
            return self._create_error_response("I'm sorry, I couldn't process your response. Please try again.")
    
    async def handle_dtmf_input(self, call_sid: str, digits: str, db: Session) -> str:
        """
        Handle DTMF (keypad) input from user
        
        Args:
            call_sid: Twilio call SID
            digits: DTMF digits pressed
            db: Database session
            
        Returns:
            TwiML response string
        """
        try:
            conversation = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
            if not conversation:
                return self._create_error_response("Conversation not found.")
            
            # Add DTMF to conversation
            conversation.conversation_json["messages"].append({
                "role": "user",
                "content": f"DTMF: {digits}",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "dtmf",
                "digits": digits
            })
            db.commit()
            
            # Handle common DTMF commands
            if digits == "0":
                return self._create_completion_response("Thank you for using our service. Goodbye!")
            elif digits == "9":
                return self._create_emergency_response()
            else:
                # Continue conversation
                return self._create_speech_gather_response(
                    message="I received your input. Please continue speaking to tell me more.",
                    action_url="/api/webhooks/twilio/voice"
                )
                
        except Exception as e:
            logger.error(f"Error handling DTMF input: {e}")
            return self._create_error_response("I'm sorry, I couldn't process your input.")
    
    async def _determine_next_action(self, conversation: Conversation, analysis: Dict[str, Any], db: Session) -> str:
        """Determine the next action based on conversation analysis"""
        try:
            urgency = analysis.get("urgency_level", "low")
            requires_immediate_attention = analysis.get("requires_immediate_attention", False)
            
            # Handle emergency situations
            if requires_immediate_attention or urgency == "critical":
                return self._create_emergency_response()
            
            # Get current state
            current_state_str = conversation.conversation_json.get("state", CallState.GREETING.value)
            current_state = CallState(current_state_str)
            
            # Determine next state
            next_state = self._get_next_state(current_state, analysis)
            
            # Update conversation state
            conversation.conversation_json["state"] = next_state.value
            db.commit()
            
            # Generate appropriate response
            if next_state == CallState.COMPLETION:
                return self._create_completion_response()
            else:
                # Get next question
                next_question = self.conversation_flow.get_next_question(
                    next_state, 
                    conversation.conversation_json.get("messages", [])
                )
                
                if next_question:
                    # Add assistant message
                    conversation.conversation_json["messages"].append({
                        "role": "assistant",
                        "content": next_question,
                        "timestamp": datetime.utcnow().isoformat(),
                        "state": next_state.value
                    })
                    db.commit()
                    
                    return self._create_speech_gather_response(
                        message=next_question,
                        action_url="/api/webhooks/twilio/voice"
                    )
                else:
                    return self._create_completion_response()
                    
        except Exception as e:
            logger.error(f"Error determining next action: {e}")
            return self._create_error_response("I'm sorry, let me ask you another question.")
    
    def _get_next_state(self, current_state: CallState, analysis: Dict[str, Any]) -> CallState:
        """Determine the next conversation state based on current state and analysis"""
        intent = analysis.get("intent", "")
        
        # State transition logic
        if current_state == CallState.GREETING:
            if intent == "pain_inquiry":
                return CallState.PAIN_ASSESSMENT
            elif intent == "wound_check":
                return CallState.WOUND_CHECK
            elif intent == "medication_question":
                return CallState.MEDICATION_CHECK
            else:
                return CallState.INITIAL_ASSESSMENT
        
        elif current_state == CallState.INITIAL_ASSESSMENT:
            return CallState.PAIN_ASSESSMENT
        
        elif current_state == CallState.PAIN_ASSESSMENT:
            return CallState.WOUND_CHECK
        
        elif current_state == CallState.WOUND_CHECK:
            return CallState.MEDICATION_CHECK
        
        elif current_state == CallState.MEDICATION_CHECK:
            return CallState.FOLLOW_UP
        
        elif current_state == CallState.FOLLOW_UP:
            return CallState.COMPLETION
        
        else:
            return CallState.COMPLETION
    
    def _get_personalized_greeting(self, patient: Patient) -> str:
        """Generate personalized greeting message"""
        # Use the patient's first name
        first_name = patient.first_name or "there"
        return f"Hello {first_name}! This is your surgical care companion calling to check on your recovery progress. I have a few questions to help monitor how you're doing. How are you feeling today?"
    
    def _create_speech_gather_response(self, message: str, action_url: str, timeout: int = None) -> str:
        """Create TwiML response with speech recognition"""
        response = VoiceResponse()
        
        gather = Gather(
            input="speech dtmf",
            timeout=timeout or self.speech_timeout,
            action=action_url,
            method="POST",
            speech_timeout="auto",
            language=self.language,
            num_digits=1
        )
        
        gather.say(message)
        response.append(gather)
        
        # Fallback if no input detected
        response.say("I didn't hear anything. Please try again or press 0 to end the call.")
        response.hangup()
        
        return str(response)
    
    def _create_completion_response(self, custom_message: str = None) -> str:
        """Create TwiML response for call completion"""
        response = VoiceResponse()
        
        message = custom_message or "Thank you for taking the time to speak with me today. Your responses have been recorded and will be reviewed by your healthcare team. If you have any urgent concerns, please contact your doctor immediately. Take care and have a great day!"
        
        response.say(message)
        response.hangup()
        
        return str(response)
    
    def _create_emergency_response(self) -> str:
        """Create TwiML response for emergency situations"""
        response = VoiceResponse()
        
        message = "Based on what you've shared, I recommend that you contact your healthcare provider immediately or call emergency services if this is urgent. Your healthcare team will be notified of this conversation. Please seek medical attention right away."
        
        response.say(message)
        response.hangup()
        
        return str(response)
    
    def _create_error_response(self, error_message: str) -> str:
        """Create TwiML response for error situations"""
        response = VoiceResponse()
        
        response.say(f"{error_message} Please try calling again later or contact your healthcare provider directly.")
        response.hangup()
        
        return str(response)
    
    def _handle_no_speech_detected(self, conversation: Conversation, db: Session) -> str:
        """Handle case when no speech is detected"""
        # Count no-speech attempts
        no_speech_count = len([
            msg for msg in conversation.conversation_json.get("messages", [])
            if msg.get("type") == "no_speech"
        ])
        
        # Add no-speech message
        conversation.conversation_json["messages"].append({
            "role": "system",
            "content": "No speech detected",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "no_speech",
            "attempt": no_speech_count + 1
        })
        db.commit()
        
        if no_speech_count >= 2:
            return self._create_completion_response("I'm having trouble hearing you. Please try calling back when you have a better connection.")
        else:
            return self._create_speech_gather_response(
                message="I didn't hear anything. Could you please repeat your response?",
                action_url="/api/webhooks/twilio/voice"
            )
    
    def _update_conversation_with_analysis(self, conversation: Conversation, analysis: Dict[str, Any]):
        """Update conversation record with analysis results"""
        conversation.intent = analysis.get("intent")
        conversation.entities = analysis.get("entities", {})
        conversation.sentiment = analysis.get("sentiment")
        conversation.urgency_level = analysis.get("urgency_level")
        conversation.symptoms = analysis.get("entities", {}).get("symptoms", [])
        conversation.pain_level = analysis.get("entities", {}).get("pain_level")
        conversation.concerns = analysis.get("entities", {}).get("concerns", [])
        conversation.actions_required = analysis.get("recommended_actions", [])
        
        # Update transcript with latest content
        user_messages = [
            msg.get("content", "") for msg in conversation.conversation_json.get("messages", [])
            if msg.get("role") == "user"
        ]
        conversation.transcript = " | ".join(user_messages)

# Global instance
twiml_service = TwiMLService()
