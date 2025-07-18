"""
Webhook Handlers API Endpoints
Handles incoming webhooks from external services, especially Twilio.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
from typing import Dict, Any
import logging
import json
from datetime import datetime

from database.connection import get_db
from models.patient import Patient
from models import Patient, VoiceInteraction, ConversationMessage

# Backward compatibility
Conversation = VoiceInteraction
from services.transcription_service import transcription_service
from services.gemini_service import gemini_service
from services.twiml_service import TwiMLService

# Create service instances
twiml_service = TwiMLService()

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio/voice", response_class=PlainTextResponse)
async def twilio_voice_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Twilio voice call webhooks
    Main entry point for voice calls
    """
    start_time = datetime.utcnow()
    call_sid = None
    form_data = None
    
    try:
        # Parse Twilio form data with timeout protection
        try:
            form_data = await request.form()
        except Exception as form_error:
            logger.error(f"Failed to parse form data: {form_error}")
            return _create_error_twiml("Unable to process your call. Please try again.")
        
        # Extract call information
        call_sid = form_data.get("CallSid", "unknown")
        from_number = form_data.get("From", "unknown")
        to_number = form_data.get("To", "unknown")
        call_status = form_data.get("CallStatus", "unknown")
        
        logger.info(f"Voice webhook START: CallSid={call_sid}, From={from_number}, Status={call_status}")
        logger.debug(f"Full form data: {dict(form_data)}")
        
        # Validate required fields
        if not call_sid or call_sid == "unknown":
            logger.error("Missing CallSid in webhook request")
            return _create_error_twiml("Call identification error. Please try again.")
        
        if not from_number or from_number == "unknown":
            logger.error("Missing From number in webhook request")
            return _create_error_twiml("Unable to identify caller. Please try again.")
        
        # Check database connection
        try:
            db.execute("SELECT 1")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
            return _create_error_twiml("Service temporarily unavailable. Please try again later.")
        
        # Find or create patient with error handling
        try:
            patient = db.query(Patient).filter(Patient.phone == from_number).first()
            if not patient:
                patient = Patient(
                    first_name="Test",
                    last_name="Patient",
                    phone=from_number,
                    email="test@example.com",
                    date_of_birth=datetime.utcnow().date(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                logger.info(f"Created test patient for {from_number}")
        except Exception as patient_error:
            logger.error(f"Patient creation/retrieval failed: {patient_error}")
            return _create_error_twiml("Unable to access patient information. Please try again.")
        
        # Handle different call scenarios with timeout monitoring
        try:
            if call_status in ["ringing", "in-progress"] and not form_data.get("SpeechResult") and not form_data.get("Digits"):
                # Initial call - start conversation
                logger.info(f"Handling incoming call for {call_sid}")
                twiml_response = await twiml_service.handle_incoming_call(call_sid, from_number, patient, db)
                
            elif form_data.get("SpeechResult") or form_data.get("UnstableSpeechResult"):
                # Speech input received
                logger.info(f"Handling speech input for {call_sid}")
                twiml_response = await twiml_service.handle_speech_input(call_sid, form_data, db)
                
            elif form_data.get("Digits"):
                # DTMF input received
                digits = form_data.get("Digits")
                logger.info(f"Handling DTMF input '{digits}' for {call_sid}")
                twiml_response = await twiml_service.handle_dtmf_input(call_sid, digits, db)
                
            else:
                # Default case - continue conversation
                logger.info(f"Handling default case for {call_sid}")
                twiml_response = await twiml_service.handle_incoming_call(call_sid, from_number, patient, db)
            
            # Validate TwiML response
            if not twiml_response or not isinstance(twiml_response, str):
                logger.error(f"Invalid TwiML response: {type(twiml_response)}")
                return _create_error_twiml("Unable to generate response. Please try again.")
            
            # Log response time
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Voice webhook COMPLETE: CallSid={call_sid}, Duration={duration:.2f}s")
            
            if duration > 10:  # Warn if processing takes more than 10 seconds
                logger.warning(f"Slow webhook processing: {duration:.2f}s for {call_sid}")
            
            return twiml_response
            
        except Exception as service_error:
            logger.error(f"TwiML service error for {call_sid}: {service_error}")
            logger.error(f"Service error type: {type(service_error).__name__}")
            return _create_error_twiml("Unable to process your request. Please try again.")
            
    except Exception as e:
        # Final catch-all error handler
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Critical webhook error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"CallSid: {call_sid}, Duration: {duration:.2f}s")
        
        if form_data:
            logger.error(f"Form data: {dict(form_data)}")
        
        return _create_error_twiml("Service temporarily unavailable. Please try again later.")


def _create_error_twiml(message: str) -> str:
    """Create a safe TwiML error response"""
    try:
        response = VoiceResponse()
        response.say(message)
        response.hangup()
        return str(response)
    except Exception as twiml_error:
        logger.error(f"Failed to create TwiML response: {twiml_error}")
        # Return minimal valid TwiML as last resort
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable. Please try again later.</Say><Hangup/></Response>'

async def handle_incoming_call(conversation: Conversation, db: Session) -> str:
    """Handle initial incoming call"""
    response = VoiceResponse()
    
    # Welcome message
    welcome_msg = f"Hello! This is your surgical care companion. I'm calling to check on your recovery progress. Let's start with a few questions."
    response.say(welcome_msg)
    
    # Ask first question using speech recognition
    gather = Gather(
        input="speech",
        timeout=10,
        action="/api/webhooks/twilio/voice",
        method="POST",
        speech_timeout="auto",
        language="en-US"
    )
    gather.say("First, how are you feeling today overall? Please describe your current condition.")
    response.append(gather)
    
    # Fallback if no input
    response.say("I didn't hear anything. Please call back when you're ready to speak.")
    response.hangup()
    
    # Update conversation
    conversation.conversation_json["messages"].append({
        "role": "assistant",
        "content": welcome_msg,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "greeting"
    })
    db.commit()
    
    return str(response)

async def handle_recorded_response(conversation: Conversation, recording_url: str, db: Session) -> str:
    """Handle recorded voice response"""
    try:
        # For now, we'll use a placeholder transcript since we're using real-time speech recognition
        # In production, this would process the recording URL if needed
        transcript_result = await transcription_service.process_recording_url(recording_url)
        transcript = transcript_result["text"]
        
        logger.info(f"Recording processed: {transcript}")
        
        # Add user message to conversation
        conversation.conversation_json["messages"].append({
            "role": "user",
            "content": transcript,
            "timestamp": datetime.utcnow().isoformat(),
            "audio_url": recording_url,
            "confidence": transcript_result["confidence"]
        })
        
        # Analyze with Gemini
        analysis = await gemini_service.analyze_conversation(
            transcript, 
            conversation.conversation_json.get("messages", [])
        )
        
        # Update conversation with analysis
        conversation.transcript = transcript
        conversation.intent = analysis.get("intent")
        conversation.entities = analysis.get("entities", {})
        conversation.sentiment = analysis.get("sentiment")
        conversation.urgency_level = analysis.get("urgency_level")
        conversation.symptoms = analysis.get("entities", {}).get("symptoms", [])
        conversation.pain_level = analysis.get("entities", {}).get("pain_level")
        conversation.concerns = analysis.get("entities", {}).get("concerns", [])
        conversation.actions_required = analysis.get("recommended_actions", [])
        
        db.commit()
        
        # Generate follow-up response
        follow_up_question = await generate_follow_up_question(analysis, conversation)
        
        response = VoiceResponse()
        
        if analysis.get("requires_immediate_attention"):
            response.say("Thank you for sharing. Based on your response, I recommend contacting your healthcare provider immediately. A nurse will be notified about your situation.")
            response.hangup()
        elif follow_up_question:
            gather = Gather(
                input="speech",
                timeout=10,
                action="/api/webhooks/twilio/voice",
                method="POST",
                speech_timeout="auto"
            )
            gather.say(follow_up_question)
            response.append(gather)
            
            response.say("I didn't hear your response. Let me ask you another question.")
        else:
            response.say("Thank you for sharing your update. Take care and don't hesitate to call if you have any concerns. Goodbye!")
            response.hangup()
            
            # Mark conversation as completed
            conversation.call_status = "completed"
            conversation.ended_at = datetime.utcnow()
            db.commit()
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error processing recorded response: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I couldn't process your response. Please try again.")
        response.hangup()
        return str(response)

async def handle_dtmf_response(conversation: Conversation, digits: str, db: Session) -> str:
    """Handle DTMF (keypad) response"""
    response = VoiceResponse()
    
    # Add DTMF response to conversation
    conversation.conversation_json["messages"].append({
        "role": "user",
        "content": f"DTMF input: {digits}",
        "timestamp": datetime.utcnow().isoformat(),
        "type": "dtmf"
    })
    
    # Simple DTMF handling (can be expanded)
    if digits == "1":
        response.say("Thank you for your response. Is there anything else you'd like to share about your recovery?")
    elif digits == "9":
        response.say("Thank you for using our service. Goodbye!")
        response.hangup()
    else:
        response.say("I didn't understand that input. Please try again or speak your response.")
    
    db.commit()
    return str(response)

async def handle_call_progress(conversation: Conversation, db: Session) -> str:
    """Handle general call progress"""
    response = VoiceResponse()
    
    # Continue conversation flow
    messages = conversation.conversation_json.get("messages", [])
    
    if len(messages) < 2:  # Still in initial phase
        gather = Gather(
            input="speech",
            timeout=10,
            action="/api/webhooks/twilio/voice",
            method="POST",
            speech_timeout="auto"
        )
        gather.say("Please tell me about any pain you're experiencing and rate it from 1 to 10.")
        response.append(gather)
        
        response.say("I didn't hear your response. Please call back when you're ready.")
        response.hangup()
    else:
        response.say("Thank you for the information. A healthcare professional will review your responses. Goodbye!")
        response.hangup()
        
        conversation.call_status = "completed"
        conversation.ended_at = datetime.utcnow()
        db.commit()
    
    return str(response)

async def generate_follow_up_question(analysis: Dict, conversation: Conversation) -> str:
    """Generate intelligent follow-up questions based on analysis"""
    intent = analysis.get("intent", "")
    entities = analysis.get("entities", {})
    pain_level = entities.get("pain_level")
    symptoms = entities.get("symptoms", [])
    
    # Question flow based on intent and entities
    if intent == "pain_inquiry" and pain_level and int(pain_level) > 6:
        return "That sounds quite uncomfortable. Are you taking your prescribed pain medication as directed?"
    elif intent == "wound_check" and any("swelling" in s.lower() or "redness" in s.lower() for s in symptoms):
        return "I'm concerned about the swelling or redness you mentioned. Has this gotten worse over the past day?"
    elif intent == "medication_question":
        return "Are you experiencing any side effects from your medications?"
    elif len(conversation.conversation_json.get("messages", [])) < 6:  # Continue if conversation is short
        return "Is there anything else about your recovery that you'd like to discuss or any questions you have?"
    
    return None  # End conversation

@router.post("/twilio/sms", response_class=PlainTextResponse)
async def twilio_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Twilio SMS webhooks
    """
    try:
        form_data = await request.form()
        
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        message_body = form_data.get("Body")
        message_sid = form_data.get("MessageSid")
        
        logger.info(f"SMS webhook: From={from_number}, Body={message_body}")
        
        # Find patient
        patient = db.query(Patient).filter(Patient.phone == from_number).first()
        
        response = MessagingResponse()
        
        if not patient:
            response.message("I'm sorry, we don't have your information in our system. Please contact your healthcare provider.")
            return str(response)
        
        # Create conversation record for SMS
        conversation = Conversation(
            id=f"sms_{message_sid}",
            patient_id=patient.id,
            call_sid=message_sid,
            phone_number=from_number,
            call_direction="inbound",
            call_status="completed",
            conversation_json={"messages": [
                {
                    "role": "user",
                    "content": message_body,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "sms"
                }
            ]},
            transcript=message_body,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow()
        )
        
        # Analyze SMS with Gemini
        analysis = await gemini_service.analyze_conversation(message_body, [])
        
        # Update conversation with analysis
        conversation.intent = analysis.get("intent")
        conversation.entities = analysis.get("entities", {})
        conversation.sentiment = analysis.get("sentiment")
        conversation.urgency_level = analysis.get("urgency_level")
        conversation.symptoms = analysis.get("entities", {}).get("symptoms", [])
        conversation.pain_level = analysis.get("entities", {}).get("pain_level")
        conversation.concerns = analysis.get("entities", {}).get("concerns", [])
        conversation.actions_required = analysis.get("recommended_actions", [])
        
        db.add(conversation)
        db.commit()
        
        # Generate response
        if analysis.get("requires_immediate_attention"):
            response.message("Thank you for your message. Based on your symptoms, please contact your healthcare provider immediately. A nurse has been notified.")
        else:
            response.message("Thank you for your update. Your information has been recorded and will be reviewed by your healthcare team. If you have urgent concerns, please call your doctor.")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"SMS webhook error: {e}")
        response = MessagingResponse()
        response.message("I'm sorry, there was an error processing your message. Please try again or contact your healthcare provider.")
        return str(response)

@router.get("/")
async def list_webhooks():
    """List available webhook endpoints"""
    return {
        "message": "Twilio Webhook Endpoints",
        "endpoints": [
            {
                "path": "/twilio/voice",
                "method": "POST",
                "description": "Handle Twilio voice call webhooks"
            },
            {
                "path": "/twilio/sms",
                "method": "POST", 
                "description": "Handle Twilio SMS webhooks"
            }
        ]
    }

async def handle_speech_recognition(conversation: Conversation, form_data: dict, db: Session) -> str:
    """Handle speech recognition result from Twilio"""
    try:
        # Extract speech recognition result
        speech_result = await transcription_service.extract_speech_from_webhook(form_data)
        transcript = speech_result["text"]
        
        if not transcript:
            # No speech detected, continue conversation
            response = VoiceResponse()
            gather = Gather(
                input="speech",
                timeout=10,
                action="/api/webhooks/twilio/voice",
                method="POST",
                speech_timeout="auto"
            )
            gather.say("I didn't hear anything. Could you please repeat your response?")
            response.append(gather)
            
            response.say("I'm having trouble hearing you. Please try calling back.")
            response.hangup()
            return str(response)
        
        logger.info(f"Speech recognition result: {transcript}")
        
        # Add user message to conversation
        conversation.conversation_json["messages"].append({
            "role": "user",
            "content": transcript,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": speech_result["confidence"],
            "source": "twilio_speech"
        })
        
        # Analyze with Gemini
        analysis = await gemini_service.analyze_conversation(
            transcript, 
            conversation.conversation_json.get("messages", [])
        )
        
        # Update conversation with analysis
        conversation.transcript = transcript
        conversation.intent = analysis.get("intent")
        conversation.entities = analysis.get("entities", {})
        conversation.sentiment = analysis.get("sentiment")
        conversation.urgency_level = analysis.get("urgency_level")
        conversation.symptoms = analysis.get("entities", {}).get("symptoms", [])
        conversation.pain_level = analysis.get("entities", {}).get("pain_level")
        conversation.concerns = analysis.get("entities", {}).get("concerns", [])
        conversation.actions_required = analysis.get("recommended_actions", [])
        
        db.commit()
        
        # Generate follow-up response
        follow_up_question = await generate_follow_up_question(analysis, conversation)
        
        response = VoiceResponse()
        
        if analysis.get("requires_immediate_attention"):
            response.say("Thank you for sharing. Based on your response, I recommend contacting your healthcare provider immediately. A nurse will be notified about your situation.")
            response.hangup()
        elif follow_up_question:
            gather = Gather(
                input="speech",
                timeout=10,
                action="/api/webhooks/twilio/voice",
                method="POST",
                speech_timeout="auto"
            )
            gather.say(follow_up_question)
            response.append(gather)
            
            response.say("I didn't hear your response. Let me ask you another question.")
        else:
            response.say("Thank you for sharing your update. Take care and don't hesitate to call if you have any concerns. Goodbye!")
            response.hangup()
            
            # Mark conversation as completed
            conversation.call_status = "completed"
            conversation.ended_at = datetime.utcnow()
            db.commit()
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error processing speech recognition: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I couldn't process your response. Please try again.")
        response.hangup()
        return str(response)