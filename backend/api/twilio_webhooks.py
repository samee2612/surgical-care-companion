"""
Twilio Webhook API Endpoints

Handles Twilio voice webhooks, audio streaming, and call status updates.
Integrates with the call orchestration service for seamless voice processing.
"""

import logging
import asyncio
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel

from services.twilio_service import get_twilio_service, AudioStreamData
from services.call_service import get_call_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class WebhookRequest(BaseModel):
    """Base webhook request model"""
    CallSid: Optional[str] = None
    From: Optional[str] = None
    To: Optional[str] = None
    CallStatus: Optional[str] = None


class VoiceWebhookRequest(WebhookRequest):
    """Voice webhook request model"""
    RecordingUrl: Optional[str] = None
    SpeechResult: Optional[str] = None
    Confidence: Optional[str] = None
    Digits: Optional[str] = None


class AudioStreamMessage(BaseModel):
    """Audio stream message model"""
    event: str
    sequenceNumber: Optional[str] = None
    media: Optional[Dict[str, Any]] = None
    start: Optional[Dict[str, Any]] = None
    stop: Optional[Dict[str, Any]] = None


@router.post("/voice-webhook/{call_session_id}")
async def voice_webhook(
    call_session_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Main voice webhook endpoint for handling Twilio voice calls
    
    Handles:
    - Initial call setup and greeting
    - Speech input processing
    - Call flow management
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        call_status = form_data.get("CallStatus")
        speech_result = form_data.get("SpeechResult")
        confidence = form_data.get("Confidence")
        digits = form_data.get("Digits")
        recording_url = form_data.get("RecordingUrl")
        
        logger.info(f"Voice webhook called for session {call_session_id}, status: {call_status}")
        
        # Get services
        twilio_service = get_twilio_service()
        call_service = get_call_service()
        
        # Handle different call states
        if call_status == "ringing":
            # Generate initial greeting TwiML
            twiml = twilio_service.generate_greeting_twiml(call_session_id, "")
            return Response(content=twiml, media_type="application/xml")
        
        elif speech_result:
            # Process speech input
            confidence_score = float(confidence or 0.0)
            
            # Process through call service
            background_tasks.add_task(
                call_service.process_speech_input,
                call_session_id,
                speech_result,
                confidence_score
            )
            
            # Generate response TwiML
            twiml = await twilio_service.process_speech_input(
                call_session_id, 
                speech_result, 
                confidence_score
            )
            return Response(content=twiml, media_type="application/xml")
        
        elif recording_url:
            # Process recorded audio
            background_tasks.add_task(
                _process_recording,
                call_session_id,
                recording_url
            )
            
            # Continue with next part of conversation
            twiml = twilio_service.generate_structured_questions_twiml(call_session_id, 0)
            return Response(content=twiml, media_type="application/xml")
        
        else:
            # Default response - start greeting
            call_context = call_service.active_sessions.get(call_session_id, {})
            initial_message = call_context.get('context_data', {}).get('initial_message', 
                                                "Hello! This is your automated follow-up call.")
            
            twiml = twilio_service.generate_greeting_twiml(call_session_id, initial_message)
            return Response(content=twiml, media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        
        # Return error TwiML
        from twilio.twiml.voice_response import VoiceResponse
        response = VoiceResponse()
        response.say("I'm sorry, we're experiencing technical difficulties. Please try again later.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@router.post("/process-speech/{call_session_id}")
async def process_speech(
    call_session_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Process speech input from gather operations
    """
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        confidence = float(form_data.get("Confidence", "0.0"))
        
        logger.info(f"Processing speech for session {call_session_id}: {speech_result}")
        
        # Get services
        twilio_service = get_twilio_service()
        call_service = get_call_service()
        
        # Process speech through call service
        result = await call_service.process_speech_input(
            call_session_id,
            speech_result,
            confidence
        )
        
        # Generate response TwiML based on result
        if result.get('next_action', {}).get('type') == 'structured_questions':
            twiml = twilio_service.generate_structured_questions_twiml(call_session_id, 0)
        else:
            twiml = await twilio_service.process_speech_input(
                call_session_id,
                speech_result,
                confidence
            )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        raise HTTPException(status_code=500, detail="Error processing speech")


@router.post("/process-answer/{call_session_id}/{question_index}")
async def process_answer(
    call_session_id: str,
    question_index: int,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Process answer to structured questions
    """
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        confidence = float(form_data.get("Confidence", "0.0"))
        
        logger.info(f"Processing answer {question_index} for session {call_session_id}: {speech_result}")
        
        # Get services
        twilio_service = get_twilio_service()
        call_service = get_call_service()
        
        # Process the answer
        await call_service.process_speech_input(
            call_session_id,
            speech_result,
            confidence
        )
        
        # Move to next question or end call
        twiml = twilio_service.generate_structured_questions_twiml(
            call_session_id, 
            question_index + 1
        )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        raise HTTPException(status_code=500, detail="Error processing answer")


@router.post("/structured-questions/{call_session_id}")
@router.post("/structured-questions/{call_session_id}/{question_index}")
async def structured_questions(
    call_session_id: str,
    question_index: int = 0
):
    """
    Generate structured questions TwiML
    """
    try:
        twilio_service = get_twilio_service()
        twiml = twilio_service.generate_structured_questions_twiml(call_session_id, question_index)
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error generating structured questions: {e}")
        raise HTTPException(status_code=500, detail="Error generating questions")


@router.post("/status-callback/{call_session_id}")
async def status_callback(
    call_session_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle call status callbacks from Twilio
    """
    try:
        form_data = await request.form()
        
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        call_duration = form_data.get("CallDuration", "0")
        
        logger.info(f"Status callback for session {call_session_id}: {call_status}")
        
        # Get services
        twilio_service = get_twilio_service()
        call_service = get_call_service()
        
        # Update call status
        await twilio_service.handle_call_status_update(
            call_sid,
            call_status,
            CallDuration=int(call_duration),
            session_id=call_session_id
        )
        
        # Handle completion
        if call_status in ['completed', 'failed', 'busy', 'no-answer']:
            background_tasks.add_task(
                call_service.complete_call,
                call_session_id
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in status callback: {e}")
        raise HTTPException(status_code=500, detail="Error processing status callback")


@router.websocket("/audio-stream/{call_session_id}")
async def audio_stream(websocket, call_session_id: str):
    """
    Handle real-time audio streaming from Twilio
    """
    try:
        await websocket.accept()
        
        twilio_service = get_twilio_service()
        call_service = get_call_service()
        
        logger.info(f"Audio stream started for session {call_session_id}")
        
        while True:
            try:
                # Receive audio stream message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("event") == "media":
                    # Process audio chunk
                    media_data = message.get("media", {})
                    payload = media_data.get("payload", "")
                    sequence_number = int(message.get("sequenceNumber", 0))
                    timestamp = message.get("timestamp", "")
                    
                    # Create audio stream data
                    stream_data = AudioStreamData(
                        call_sid=call_session_id,  # Using session ID as call SID for simplicity
                        sequence_number=sequence_number,
                        timestamp=timestamp,
                        payload=payload,
                        track="inbound"
                    )
                    
                    # Process through Twilio service
                    transcription = await twilio_service.process_audio_stream(
                        call_session_id,
                        stream_data
                    )
                    
                    # If we have transcription, send to call service
                    if transcription and transcription.text.strip():
                        await call_service.process_speech_input(
                            call_session_id,
                            transcription.text,
                            transcription.confidence
                        )
                
                elif message.get("event") == "start":
                    logger.info(f"Audio stream start event for {call_session_id}")
                    
                elif message.get("event") == "stop":
                    logger.info(f"Audio stream stop event for {call_session_id}")
                    break
                    
            except Exception as e:
                logger.error(f"Error processing audio stream message: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in audio stream: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/call-status/{call_session_id}")
async def get_call_status(call_session_id: str):
    """
    Get current call status and information
    """
    try:
        call_service = get_call_service()
        twilio_service = get_twilio_service()
        
        # Get session info from call service
        session_info = call_service.active_sessions.get(call_session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Get call context from Twilio service
        call_context = twilio_service.get_call_context(session_info.get('call_sid', ''))
        
        return {
            'call_session_id': call_session_id,
            'status': session_info.get('phase', 'unknown'),
            'twilio_status': session_info.get('twilio_status', 'unknown'),
            'duration_seconds': (datetime.now() - session_info['started_at']).total_seconds(),
            'transcripts_count': len(session_info.get('transcripts', [])),
            'ai_responses_count': len(session_info.get('ai_responses', [])),
            'clinical_data': session_info.get('clinical_data', {}),
            'call_context': call_context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving call status")


@router.get("/call-transcripts/{call_session_id}")
async def get_call_transcripts(call_session_id: str):
    """
    Get all transcripts for a call session
    """
    try:
        call_service = get_call_service()
        
        session_info = call_service.active_sessions.get(call_session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        return {
            'call_session_id': call_session_id,
            'transcripts': session_info.get('transcripts', []),
            'ai_responses': session_info.get('ai_responses', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcripts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transcripts")


async def _process_recording(call_session_id: str, recording_url: str) -> None:
    """
    Background task to process call recording
    """
    try:
        # Get services
        from services.speech_to_text import get_stt_service
        stt_service = get_stt_service()
        call_service = get_call_service()
        
        # Transcribe recording
        transcription_result = await stt_service.transcribe_url(recording_url)
        
        # Process through call service
        if transcription_result.get('text'):
            await call_service.process_speech_input(
                call_session_id,
                transcription_result['text'],
                transcription_result.get('confidence', 0.8)
            )
        
        logger.info(f"Processed recording for session {call_session_id}")
        
    except Exception as e:
        logger.error(f"Error processing recording: {e}")


# Note: Middleware should be added to the main FastAPI app, not individual routers
# This function is available for use in main.py if needed
async def validate_twilio_request(request: Request, call_next):
    """
    Middleware function to validate Twilio webhook requests
    Can be applied in main.py using @app.middleware("http")
    """
    # In production, implement Twilio signature validation here
    # For now, just pass through
    response = await call_next(request)
    return response
