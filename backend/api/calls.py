"""
Call Management API Endpoints
Handles call initiation, monitoring, and management with Twilio integration.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from services.call_service import get_call_service
from services.twilio_service import get_twilio_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class InitiateCallRequest(BaseModel):
    """Request model for call initiation"""
    patient_id: str
    call_session_id: str
    call_type: str = "followup"
    priority: str = "normal"


class InitiateCallResponse(BaseModel):
    """Response model for call initiation"""
    call_session_id: str
    call_sid: Optional[str]
    status: str
    message: str
    webhook_url: Optional[str] = None


class CallStatusResponse(BaseModel):
    """Response model for call status"""
    call_session_id: str
    status: str
    phase: str
    duration_seconds: int
    transcripts_count: int
    ai_responses_count: int
    clinical_data: Dict[str, Any]


@router.get("/")
async def list_calls(db: Session = Depends(get_db)):
    """List all calls with status information"""
    try:
        # Get active calls from call service
        call_service = get_call_service()
        active_sessions = call_service.active_sessions
        
        # Format response
        calls_list = []
        for session_id, session_data in active_sessions.items():
            calls_list.append({
                'call_session_id': session_id,
                'patient_id': session_data.get('patient_id'),
                'status': session_data.get('phase', 'unknown').value if hasattr(session_data.get('phase'), 'value') else str(session_data.get('phase', 'unknown')),
                'started_at': session_data.get('started_at'),
                'call_sid': session_data.get('call_sid'),
                'call_type': session_data.get('call_context', {}).call_type.value if hasattr(session_data.get('call_context', {}), 'call_type') else 'unknown',
                'duration_seconds': (datetime.now() - session_data['started_at']).total_seconds() if session_data.get('started_at') else 0
            })
        
        return {
            'active_calls': calls_list,
            'total_active': len(calls_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving calls")


@router.post("/initiate", response_model=InitiateCallResponse)
async def initiate_call(
    request: InitiateCallRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Initiate a new voice call to a patient"""
    try:
        logger.info(f"Initiating call for patient {request.patient_id}, session {request.call_session_id}")
        
        # Get call service
        call_service = get_call_service()
        
        # Initiate call asynchronously
        call_result = await call_service.initiate_patient_call(
            patient_id=request.patient_id,
            call_session_id=request.call_session_id,
            call_type=request.call_type
        )
        
        # Generate webhook URL
        webhook_url = f"{settings.TWILIO_WEBHOOK_URL or 'https://your-ngrok-url.com'}/api/v1/twilio/voice-webhook/{request.call_session_id}"
        
        return InitiateCallResponse(
            call_session_id=call_result.call_session_id,
            call_sid=call_result.call_sid,
            status=call_result.status,
            message=f"Call initiated successfully to patient {request.patient_id}",
            webhook_url=webhook_url
        )
        
    except ValueError as e:
        logger.error(f"Validation error initiating call: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate call")


@router.get("/status/{call_session_id}", response_model=CallStatusResponse)
async def get_call_status(call_session_id: str):
    """Get detailed status of a specific call"""
    try:
        call_service = get_call_service()
        
        # Get session info
        session_info = call_service.active_sessions.get(call_session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Calculate duration
        duration = (datetime.now() - session_info['started_at']).total_seconds()
        
        return CallStatusResponse(
            call_session_id=call_session_id,
            status=session_info.get('twilio_status', 'unknown'),
            phase=session_info.get('phase', 'unknown').value if hasattr(session_info.get('phase'), 'value') else str(session_info.get('phase', 'unknown')),
            duration_seconds=int(duration),
            transcripts_count=len(session_info.get('transcripts', [])),
            ai_responses_count=len(session_info.get('ai_responses', [])),
            clinical_data=session_info.get('clinical_data', {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving call status")


@router.get("/transcripts/{call_session_id}")
async def get_call_transcripts(call_session_id: str):
    """Get all transcripts and AI responses for a call"""
    try:
        call_service = get_call_service()
        
        session_info = call_service.active_sessions.get(call_session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        return {
            'call_session_id': call_session_id,
            'transcripts': session_info.get('transcripts', []),
            'ai_responses': session_info.get('ai_responses', []),
            'clinical_data': session_info.get('clinical_data', {}),
            'conversation_flow': [
                {
                    'type': 'user_input',
                    'content': transcript['text'],
                    'timestamp': transcript['timestamp'],
                    'confidence': transcript.get('confidence', 0)
                }
                for transcript in session_info.get('transcripts', [])
            ] + [
                {
                    'type': 'ai_response',
                    'content': response['response'],
                    'timestamp': response['timestamp']
                }
                for response in session_info.get('ai_responses', [])
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcripts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transcripts")


@router.post("/complete/{call_session_id}")
async def complete_call(call_session_id: str):
    """Manually complete a call session"""
    try:
        call_service = get_call_service()
        
        # Complete the call
        result = await call_service.complete_call(call_session_id)
        
        return {
            'call_session_id': call_session_id,
            'status': 'completed',
            'duration_seconds': result.duration_seconds,
            'summary': result.conversation_summary,
            'clinical_alerts': result.clinical_alerts,
            'next_call_scheduled': result.next_call_scheduled
        }
        
    except ValueError as e:
        logger.error(f"Error completing call: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing call: {e}")
        raise HTTPException(status_code=500, detail="Error completing call")


@router.get("/twilio-status")
async def get_twilio_status():
    """Get Twilio service status and configuration"""
    try:
        twilio_service = get_twilio_service()
        
        return {
            'status': 'connected',
            'phone_number': settings.TWILIO_PHONE_NUMBER,
            'webhook_base_url': settings.TWILIO_WEBHOOK_URL or 'Not configured',
            'active_calls_count': len(twilio_service.active_calls),
            'configuration': {
                'account_sid_configured': bool(settings.TWILIO_ACCOUNT_SID),
                'auth_token_configured': bool(settings.TWILIO_AUTH_TOKEN),
                'phone_number_configured': bool(settings.TWILIO_PHONE_NUMBER),
                'webhook_url_configured': bool(settings.TWILIO_WEBHOOK_URL)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Twilio status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'configuration': {
                'account_sid_configured': bool(settings.TWILIO_ACCOUNT_SID),
                'auth_token_configured': bool(settings.TWILIO_AUTH_TOKEN),
                'phone_number_configured': bool(settings.TWILIO_PHONE_NUMBER),
                'webhook_url_configured': bool(settings.TWILIO_WEBHOOK_URL)
            }
        }


@router.get("/analytics")
async def get_call_analytics():
    """Get call analytics and statistics"""
    try:
        call_service = get_call_service()
        
        # Get notification service for alert statistics
        from services.notification_service import get_notification_service
        notification_service = get_notification_service()
        
        active_sessions = call_service.active_sessions
        
        # Calculate statistics
        total_active = len(active_sessions)
        call_phases = {}
        call_types = {}
        total_duration = 0
        
        for session_data in active_sessions.values():
            # Phase statistics
            phase = str(session_data.get('phase', 'unknown'))
            call_phases[phase] = call_phases.get(phase, 0) + 1
            
            # Call type statistics
            call_context = session_data.get('call_context', {})
            call_type = call_context.call_type.value if hasattr(call_context, 'call_type') else 'unknown'
            call_types[call_type] = call_types.get(call_type, 0) + 1
            
            # Duration
            if session_data.get('started_at'):
                duration = (datetime.now() - session_data['started_at']).total_seconds()
                total_duration += duration
        
        # Get alert statistics
        alert_stats = notification_service.get_alert_statistics()
        
        return {
            'active_calls': {
                'total': total_active,
                'by_phase': call_phases,
                'by_type': call_types,
                'average_duration_minutes': (total_duration / total_active / 60) if total_active > 0 else 0
            },
            'alerts': alert_stats,
            'system_health': {
                'twilio_connected': True,  # Would check actual connection
                'stt_service_available': True,  # Would check actual service
                'ai_service_available': True   # Would check actual service
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")
