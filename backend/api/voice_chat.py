"""
Voice Chat API for TKA Patients
Enhanced with call context system for structured conversations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from database.connection import get_db
from models.patient import Patient
from models.call_session import CallSession
from services.voice_chat import get_chat_service
from services.call_context_service import CallContextService
from services.context_injection_service import ContextInjectionService

router = APIRouter()

class ContextualChatMessage(BaseModel):
    message: str
    patient_id: str
    call_session_id: str
    # Removed conversation_history - now handled automatically by backend

class ChatResponse(BaseModel):
    response: str
    context_metadata: dict

class StartCallRequest(BaseModel):
    patient_id: str
    call_session_id: str

class StartCallResponse(BaseModel):
    initial_message: str
    call_context: dict

# Initialize context services
context_service = CallContextService()
injection_service = ContextInjectionService()

@router.post("/contextual-chat", response_model=ChatResponse)
async def contextual_chat(chat_msg: ContextualChatMessage, db: Session = Depends(get_db)):
    """Context-aware chat using call session information with automatic conversation history"""
    try:
        # Get patient and call session
        patient = db.query(Patient).filter(Patient.id == chat_msg.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        call_session = db.query(CallSession).filter(CallSession.id == chat_msg.call_session_id).first()
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Load conversation history from database (or start new)
        if call_session.conversation_history:
            history = json.loads(call_session.conversation_history)
        else:
            history = []
        
        # Append the new user message
        history.append({"role": "user", "content": chat_msg.message})
        
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
            conversation_history=history
        )
        
        # Append the assistant's response to history
        history.append({"role": "assistant", "content": response})
        
        # Save updated history back to database
        call_session.conversation_history = json.dumps(history)
        db.commit()
        
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
        
        # Initialize conversation history with the first assistant message
        history = [{"role": "assistant", "content": initial_response}]
        call_session.conversation_history = json.dumps(history)
        
        # Update call session status
        call_session.call_status = "in_progress"
        call_session.actual_call_start = datetime.now()
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