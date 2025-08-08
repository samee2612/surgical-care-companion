import os
import asyncio
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

LIVEKIT_URL = os.getenv('LIVEKIT_URL')
LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
SIP_TRUNK_ID = os.getenv('SIP_TRUNK_ID')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

class CallRequest(BaseModel):
    patient_id: str
    call_session_id: str
    phone_number: str

@app.post("/call_phone")
async def call_phone(request: CallRequest):
    # Validate phone number
    if not request.phone_number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must be in E.164 format (e.g., +1XXXXXXXXXX).")

    # Validate environment variables
    missing_vars = [v for v in ['LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'SIP_TRUNK_ID', 'TWILIO_PHONE_NUMBER'] if not os.getenv(v)]
    if missing_vars:
        raise HTTPException(status_code=500, detail=f"Missing environment variables: {', '.join(missing_vars)}. Please check your .env file.")

    try:
        from livekit import api
        livekit_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        timestamp = int(asyncio.get_event_loop().time())
        room_name = f"surgical-call-{timestamp}"
        await livekit_api.room.create_room(api.CreateRoomRequest(name=room_name))
        await livekit_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="surgical-care-assistant",
                metadata=json.dumps({
                    "phone_number": request.phone_number,
                    "patient_id": request.patient_id,
                    "call_session_id": request.call_session_id
                })
            )
        )
        await livekit_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_number=TWILIO_PHONE_NUMBER,
                sip_call_to=request.phone_number,
                room_name=room_name,
                participant_identity=f"caller-{timestamp}",
                participant_name="Web Caller"
            )
        )
        await livekit_api.aclose()
        return {"message": f"Call initiated to {request.phone_number} successfully!"}
    except Exception as e:
        try:
            await livekit_api.aclose()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error initiating call: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("call_phone:app", host="0.0.0.0", port=8002, reload=True)