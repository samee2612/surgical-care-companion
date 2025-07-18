"""
TwiML Service API Endpoints
Standalone API for testing and interacting with the TwiML service
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

from database.connection import get_db
from models.patient import Patient
from models import Patient, VoiceInteraction

# Backward compatibility
Conversation = VoiceInteraction
from services.twiml_service import twiml_service, CallState
from services.gemini_service import gemini_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/test/voice-call", response_class=PlainTextResponse)
async def test_voice_call(
    phone_number: str,
    call_sid: str = None,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for simulating a voice call
    
    Args:
        phone_number: Patient phone number
        call_sid: Test call SID (auto-generated if not provided)
        db: Database session
        
    Returns:
        TwiML response for testing
    """
    if call_sid is None:
        # Generate unique call_sid for testing
        call_sid = f"test_call_{int(datetime.now().timestamp())}"
    try:
        # Find or create test patient
        patient = db.query(Patient).filter(Patient.phone == phone_number).first()
        if not patient:
            # Create test patient
            patient = Patient(
                mrn=f"TEST_{phone_number.replace('+', '').replace('-', '')}",
                first_name="Test",
                last_name="Patient",
                phone=phone_number,
                voice_consent_given=True,
                data_consent_given=True,
                program_active=True
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        
        # Handle incoming call
        twiml_response = await twiml_service.handle_incoming_call(call_sid, phone_number, patient, db)
        
        return twiml_response
        
    except Exception as e:
        logger.error(f"Test voice call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/speech-input", response_class=PlainTextResponse)
async def test_speech_input(
    call_sid: str,
    speech_text: str,
    confidence: float = 0.9,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for simulating speech input
    
    Args:
        call_sid: Call SID
        speech_text: Simulated speech text
        confidence: Speech confidence score
        db: Database session
        
    Returns:
        TwiML response for testing
    """
    try:
        # Create mock form data
        form_data = {
            "CallSid": call_sid,
            "SpeechResult": speech_text,
            "Confidence": str(confidence)
        }
        
        # Handle speech input
        twiml_response = await twiml_service.handle_speech_input(call_sid, form_data, db)
        
        return twiml_response
        
    except Exception as e:
        logger.error(f"Test speech input error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/dtmf-input", response_class=PlainTextResponse)
async def test_dtmf_input(
    call_sid: str,
    digits: str,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for simulating DTMF input
    
    Args:
        call_sid: Call SID
        digits: DTMF digits
        db: Database session
        
    Returns:
        TwiML response for testing
    """
    try:
        twiml_response = await twiml_service.handle_dtmf_input(call_sid, digits, db)
        
        return twiml_response
        
    except Exception as e:
        logger.error(f"Test DTMF input error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/conversation/{call_sid}")
async def get_test_conversation(call_sid: str, db: Session = Depends(get_db)):
    """
    Get conversation details for testing
    
    Args:
        call_sid: Call SID
        db: Database session
        
    Returns:
        Conversation details
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "id": conversation.id,
            "call_sid": conversation.call_sid,
            "phone_number": conversation.phone_number,
            "call_status": conversation.call_status,
            "state": conversation.conversation_json.get("state"),
            "message_count": len(conversation.conversation_json.get("messages", [])),
            "messages": conversation.conversation_json.get("messages", []),
            "transcript": conversation.transcript,
            "intent": conversation.intent,
            "sentiment": conversation.sentiment,
            "urgency_level": conversation.urgency_level,
            "symptoms": conversation.symptoms,
            "pain_level": conversation.pain_level,
            "concerns": conversation.concerns,
            "actions_required": conversation.actions_required,
            "started_at": conversation.started_at,
            "ended_at": conversation.ended_at
        }
        
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/analyze-text")
async def test_analyze_text(
    text: str,
    conversation_history: Optional[list] = None
):
    """
    Test endpoint for analyzing text with Gemini
    
    Args:
        text: Text to analyze
        conversation_history: Optional conversation history
        
    Returns:
        Analysis results
    """
    try:
        analysis = await gemini_service.analyze_conversation(text, conversation_history or [])
        
        return {
            "input_text": text,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test analyze text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/conversation-flow")
async def get_conversation_flow():
    """
    Get conversation flow information for testing
    
    Returns:
        Conversation flow details
    """
    try:
        return {
            "states": [state.value for state in CallState],
            "speech_timeout": twiml_service.speech_timeout,
            "max_speech_time": twiml_service.max_speech_time,
            "language": twiml_service.language,
            "question_flows": {
                state.value: twiml_service.conversation_flow.question_flows.get(state, [])
                for state in CallState
            }
        }
        
    except Exception as e:
        logger.error(f"Get conversation flow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate/full-conversation")
async def simulate_full_conversation(
    phone_number: str,
    responses: list,
    db: Session = Depends(get_db)
):
    """
    Simulate a full conversation flow for testing
    
    Args:
        phone_number: Patient phone number
        responses: List of simulated patient responses
        db: Database session
        
    Returns:
        Full conversation simulation results
    """
    try:
        call_sid = f"sim_call_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        conversation_log = []
        
        # Find or create test patient
        patient = db.query(Patient).filter(Patient.phone == phone_number).first()
        if not patient:
            patient = Patient(
                mrn=f"TEST_{phone_number.replace('+', '').replace('-', '')}",
                first_name="Test",
                last_name="Patient",
                phone=phone_number,
                voice_consent_given=True,
                data_consent_given=True,
                program_active=True
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        
        # Start conversation
        initial_response = await twiml_service.handle_incoming_call(call_sid, phone_number, patient, db)
        conversation_log.append({
            "step": "initial",
            "twiml": initial_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Process each response
        for i, response_text in enumerate(responses):
            form_data = {
                "CallSid": call_sid,
                "SpeechResult": response_text,
                "Confidence": "0.9"
            }
            
            twiml_response = await twiml_service.handle_speech_input(call_sid, form_data, db)
            conversation_log.append({
                "step": f"response_{i+1}",
                "input": response_text,
                "twiml": twiml_response,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Get final conversation state
        final_conversation = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
        
        return {
            "call_sid": call_sid,
            "phone_number": phone_number,
            "conversation_log": conversation_log,
            "final_state": {
                "state": final_conversation.conversation_json.get("state") if final_conversation else None,
                "message_count": len(final_conversation.conversation_json.get("messages", [])) if final_conversation else 0,
                "intent": final_conversation.intent if final_conversation else None,
                "urgency_level": final_conversation.urgency_level if final_conversation else None,
                "symptoms": final_conversation.symptoms if final_conversation else [],
                "pain_level": final_conversation.pain_level if final_conversation else None
            }
        }
        
    except Exception as e:
        logger.error(f"Simulate conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_twiml_endpoints():
    """List all TwiML service endpoints"""
    return {
        "message": "TwiML Service API Endpoints",
        "endpoints": [
            {
                "path": "/test/voice-call",
                "method": "POST",
                "description": "Test voice call initiation",
                "parameters": ["phone_number", "call_sid (optional)"]
            },
            {
                "path": "/test/speech-input",
                "method": "POST",
                "description": "Test speech input processing",
                "parameters": ["call_sid", "speech_text", "confidence (optional)"]
            },
            {
                "path": "/test/dtmf-input",
                "method": "POST",
                "description": "Test DTMF input processing",
                "parameters": ["call_sid", "digits"]
            },
            {
                "path": "/test/conversation/{call_sid}",
                "method": "GET",
                "description": "Get conversation details"
            },
            {
                "path": "/test/analyze-text",
                "method": "POST",
                "description": "Test text analysis with Gemini",
                "parameters": ["text", "conversation_history (optional)"]
            },
            {
                "path": "/test/conversation-flow",
                "method": "GET",
                "description": "Get conversation flow information"
            },
            {
                "path": "/simulate/full-conversation",
                "method": "POST",
                "description": "Simulate full conversation flow",
                "parameters": ["phone_number", "responses (list)"]
            }
        ]
    }
