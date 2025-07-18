"""
Call Management API Endpoints
Handles call initiation, monitoring, and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class CallRequest(BaseModel):
    to_number: str
    from_number: Optional[str] = None
    webhook_url: Optional[str] = None

@router.get("/")
async def list_calls():
    """List all calls - TODO: Implement"""
    return {"message": "Call management endpoints - Coming soon"}

@router.post("/test-call")
async def make_test_call(call_request: CallRequest):
    """Make a test call using Twilio API"""
    
    try:
        # Import Twilio client
        from twilio.rest import Client
        
        # Get credentials from environment
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        default_from_number = os.getenv('TWILIO_PHONE_NUMBER')
        webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        
        if not all([account_sid, auth_token, default_from_number]):
            raise HTTPException(
                status_code=500,
                detail="Missing Twilio credentials in environment variables"
            )
        
        # Use provided numbers or defaults
        from_number = call_request.from_number or default_from_number
        webhook_url = call_request.webhook_url or f"{webhook_base_url}/api/webhooks/twilio/voice"
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Make the call
        call = client.calls.create(
            url=webhook_url,
            to=call_request.to_number,
            from_=from_number,
            method='POST',
            timeout=60,
            record=False
        )
        
        logger.info(f"Call initiated: {call.sid} to {call_request.to_number}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "from": from_number,
            "to": call_request.to_number,
            "webhook_url": webhook_url,
            "message": f"Call initiated to {call_request.to_number}"
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Twilio package not installed. Please install with: pip install twilio"
        )
    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make call: {str(e)}"
        )

@router.post("/initiate")
async def initiate_call():
    """Initiate a call - TODO: Implement"""
    return {"message": "Call initiation - Coming soon"}
