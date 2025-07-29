# surgicalcompanian/backend/models/chat_models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ConverseRequest(BaseModel):
    patient_id: str
    call_session_id: str
    message: Optional[str] = None # Patient's latest message, can be empty for first turn

class ChatResponse(BaseModel):
    # The 'response' field that was in your original FastAPi/Flask code
    response: str
    state: str
    
    # Metadata for debugging or context (matches what your orchestrator returns in debug_info)
    context_metadata: Dict[str, Any] 
    
    # These fields ensure the API response includes the updated state
    current_call_status: str 
    extracted_report: Dict[str, Any]

class StartRequest(BaseModel):
    patient_id: str