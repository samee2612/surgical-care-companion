"""
Voice Chat API for TKA Patients
Enhanced with call context system for structured conversations and conversation manager integration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database.connection import get_db
from models.patient import Patient
from models.call_session import CallSession
from services.voice_chat import get_chat_service
from services.call_context_service import get_call_context_service
from services.context_injection_service import get_context_injection_service
from services.conversation_manager import get_conversation_manager

router = APIRouter()

class ContextualChatMessage(BaseModel):
    message: str
    patient_id: str
    call_session_id: str
    conversation_history: Optional[list] = []

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    context_metadata: Optional[dict] = None
    risk_level: Optional[str] = None
    escalation_needed: Optional[bool] = False

class StartCallRequest(BaseModel):
    patient_id: str
    call_session_id: str

class StartCallResponse(BaseModel):
    initial_message: str
    call_context: dict
    session_key: str
    status: str = "success"

class ConversationFlowMessage(BaseModel):
    message: str
    session_key: str

class ConversationFlowResponse(BaseModel):
    response: str
    status: str
    risk_level: Optional[str] = None
    escalation_needed: Optional[bool] = False
    conversation_state: Optional[dict] = None

# Initialize context services (use factory functions)
context_service = get_call_context_service()
injection_service = get_context_injection_service()
conversation_manager = get_conversation_manager()

@router.post("/start-conversation-flow", response_model=StartCallResponse)
async def start_conversation_flow(request: StartCallRequest, db: Session = Depends(get_db)):
    """Start a structured conversation using the conversation manager"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == request.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Start conversation using conversation manager
        result = conversation_manager.start_conversation(patient, call_session)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return StartCallResponse(
            initial_message=result['initial_message'],
            call_context=result['call_context'],
            session_key=result['session_key']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start conversation error: {str(e)}")

@router.post("/conversation-flow", response_model=ConversationFlowResponse)
async def conversation_flow(message: ConversationFlowMessage):
    """Process message through conversation flow"""
    try:
        result = conversation_manager.process_message(message.session_key, message.message)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ConversationFlowResponse(
            response=result['response'],
            status=result['status'],
            risk_level=result.get('risk_level'),
            escalation_needed=result.get('escalation_needed', False),
            conversation_state=result.get('conversation_state')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation flow error: {str(e)}")

@router.get("/conversation-status/{session_key}")
async def get_conversation_status(session_key: str):
    """Get current conversation flow status"""
    try:
        status = conversation_manager.get_flow_status(session_key)
        if not status:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")

@router.post("/end-conversation/{session_key}")
async def end_conversation(session_key: str):
    """End conversation and clean up"""
    try:
        result = conversation_manager.end_conversation(session_key)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"End conversation error: {str(e)}")

@router.post("/contextual-chat", response_model=ChatResponse)
async def contextual_chat(chat_msg: ContextualChatMessage, db: Session = Depends(get_db)):
    """Context-aware chat using call session information (legacy endpoint for compatibility)"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == chat_msg.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == chat_msg.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Generate call context
        call_context = context_service.get_call_context(patient, call_session)
        
        # Generate LLM prompt with context (ongoing conversation)
        prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=False)
        
        # Get chat service and generate response with context
        chat_service = get_chat_service()
        response = await chat_service.generate_contextual_response(
            user_message=chat_msg.message,
            system_prompt=prompt_data["system_prompt"],
            context_metadata=prompt_data["context_metadata"],
            conversation_history=chat_msg.conversation_history
        )
        
        return ChatResponse(
            response=response,
            context_metadata=prompt_data["context_metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contextual chat error: {str(e)}")

@router.post("/start-call", response_model=StartCallResponse)
async def start_call(request: StartCallRequest, db: Session = Depends(get_db)):
    """Start a structured call with proper context injection"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == request.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Generate call context
        call_context = context_service.get_call_context(patient, call_session)
        
        # Generate initial prompt (start of conversation)
        prompt_data = injection_service.generate_llm_prompt(call_context, is_initial_call=True)
        
        # Get chat service and start conversation
        chat_service = get_chat_service()
        initial_response = await chat_service.start_contextual_conversation(
            system_prompt=prompt_data["system_prompt"],
            user_prompt=prompt_data["user_prompt"],
            context_metadata=prompt_data["context_metadata"]
        )
        
        # Update call session status
        db.query(CallSession).filter(CallSession.id == request.call_session_id).update({
            "call_status": "in_progress",
            "actual_call_start": datetime.now()
        })
        db.commit()
        
        return StartCallResponse(
            initial_message=initial_response,
            call_context={
                "call_type": call_context.call_type.value,
                "days_from_surgery": call_context.days_from_surgery,
                "estimated_duration": call_context.estimated_duration_minutes,
                "focus_areas": call_context.focus_areas
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting call: {str(e)}")

@router.get("/patients/{patient_id}/calls/next")
async def get_next_scheduled_call(patient_id: str, db: Session = Depends(get_db)):
    """Get the next scheduled call for a patient"""
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get next scheduled call
        call_session = db.query(CallSession).filter(
            CallSession.patient_id == patient.id,
            CallSession.call_status == "scheduled"
        ).order_by(CallSession.scheduled_date).first()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="No scheduled calls found")
        
        return {
            "patient_id": patient.id,
            "patient_name": patient.name,
            "call_session_id": call_session.id,
            "call_type": call_session.call_type,
            "days_from_surgery": call_session.days_from_surgery,
            "scheduled_date": call_session.scheduled_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting next call: {str(e)}")