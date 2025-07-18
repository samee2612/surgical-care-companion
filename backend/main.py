"""
TKA Voice Agent - Main FastAPI Application

Entry point for the TKA Voice Agent API server.
"""

from fastapi import FastAPI, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from api.patients import router as patients_router
from api.calls import router as calls_router
from api.webhooks import router as webhooks_router
from api.clinical import router as clinical_router
from api.voice_chat import router as voice_chat_router
from api.conversations import router as conversations_router
from api.twiml_api import router as twiml_router
from database.connection import engine, create_tables

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TKA Voice Agent API",
    description="AI-powered voice agent for post-surgical patient monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    patients_router,
    prefix=f"{settings.API_V1_STR}/patients",
    tags=["patients"]
)

app.include_router(
    calls_router,
    prefix=f"{settings.API_V1_STR}/calls",
    tags=["calls"]
)

app.include_router(
    webhooks_router,
    prefix="/api/webhooks",
    tags=["webhooks"]
)

app.include_router(
    clinical_router,
    prefix=f"{settings.API_V1_STR}/clinical",
    tags=["clinical"]
)

app.include_router(
    voice_chat_router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["voice-chat"]
)

app.include_router(
    conversations_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["conversations"]
)

app.include_router(
    twiml_router,
    prefix="/twiml",
    tags=["twiml"]
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting TKA Voice Agent API...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("TKA Voice Agent API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down TKA Voice Agent API...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TKA Voice Agent API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with TwiML support for webhooks."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    
    # Check if this is a Twilio webhook request
    if "/twilio" in str(request.url):
        logger.error("Returning TwiML error response for Twilio webhook")
        # Return TwiML response for Twilio webhooks
        twiml_response = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service temporarily unavailable. Please try again later.</Say><Hangup/></Response>'
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Return JSON response for non-webhook requests
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Add simple test endpoint before the routers
@app.post("/api/webhooks/twilio/simple-test")
async def simple_twiml_test(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    SpeechResult: str = Form(None),
    Digits: str = Form(None)
):
    """Simple TwiML test endpoint with dummy responses - no Gemini, no database"""
    
    logger.info(f"Simple test webhook: CallSid={CallSid}, From={From}, Status={CallStatus}")
    
    if SpeechResult:
        logger.info(f"Speech detected: '{SpeechResult}'")
    if Digits:
        logger.info(f"DTMF detected: '{Digits}'")
    
    # Generate simple TwiML response
    twiml = generate_simple_twiml_response(CallStatus, SpeechResult, Digits)
    
    return Response(content=twiml, media_type="application/xml")

def generate_simple_twiml_response(call_status: str, speech: str = None, digits: str = None) -> str:
    """Generate simple TwiML responses for testing"""
    
    if call_status == "ringing":
        return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! This is a simple test system. Say hello or press 1.</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">I'm listening...</Say>
    </Gather>
    <Say voice="alice">No response. Goodbye!</Say>
    <Hangup />
</Response>"""
    
    if speech:
        speech_lower = speech.lower().strip()
        
        if "hello" in speech_lower or "hi" in speech_lower:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Nice to hear from you. Say help for options or goodbye to end.</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">What would you like to do?</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif "help" in speech_lower:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Options: Say status for system check, test to run diagnostics, or goodbye to end.</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Choose an option...</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif "status" in speech_lower:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">System status: All services running. Simple test mode active. Everything working!</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Anything else?</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif "test" in speech_lower:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Running test... Beep beep beep... Test successful! All systems go!</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Test complete!</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif "goodbye" in speech_lower or "bye" in speech_lower:
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Goodbye! Thanks for testing. Have a great day!</Say>
    <Hangup />
</Response>"""
        
        else:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">You said {speech}. That's interesting! Say help for options.</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Try again...</Say>
    </Gather>
    <Hangup />
</Response>"""
    
    if digits:
        if digits == "1":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">You pressed 1. Main menu: Press 2 for help, 3 for status, 9 to end.</Say>
    <Gather input="dtmf" timeout="10" numDigits="1" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Press a key...</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif digits == "2":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Help: Press 1 for menu, 3 for status, 4 for test, 9 to hang up.</Say>
    <Gather input="dtmf" timeout="10" numDigits="1" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Choose option...</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif digits == "3":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Status check: All systems running, test mode active. Press any key.</Say>
    <Gather input="dtmf" timeout="10" numDigits="1" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Press a key...</Say>
    </Gather>
    <Hangup />
</Response>"""
        
        elif digits == "9":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for testing! Goodbye!</Say>
    <Hangup />
</Response>"""
        
        else:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">You pressed {digits}. Press 1 for menu, 2 for help, 9 to end.</Say>
    <Gather input="dtmf" timeout="10" numDigits="1" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Try again...</Say>
    </Gather>
    <Hangup />
</Response>"""
    
    # Default response
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Simple test system ready. Say hello or press 1 to begin.</Say>
    <Gather input="speech dtmf" timeout="10" speechTimeout="3" action="/api/webhooks/twilio/simple-test" method="POST">
        <Say voice="alice">Waiting for input...</Say>
    </Gather>
    <Say voice="alice">No response. Goodbye!</Say>
    <Hangup />
</Response>"""

# Add Gemini-powered endpoint after the simple test endpoint
@app.post("/api/webhooks/twilio/gemini-test")
async def gemini_twiml_test(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    SpeechResult: str = Form(None),
    Digits: str = Form(None)
):
    """Gemini-powered TwiML endpoint - real AI responses"""
    
    logger.info(f"Gemini test webhook: CallSid={CallSid}, From={From}, Status={CallStatus}")
    
    if SpeechResult:
        logger.info(f"Speech detected: '{SpeechResult}'")
    if Digits:
        logger.info(f"DTMF detected: '{Digits}'")
    
    # Generate Gemini-powered TwiML response
    twiml = await generate_gemini_twiml_response(CallStatus, SpeechResult, Digits)
    
    return Response(content=twiml, media_type="application/xml")

async def generate_gemini_twiml_response(call_status: str, speech: str = None, digits: str = None) -> str:
    """Generate TwiML responses using Gemini AI"""
    
    # Import Gemini service
    from services.gemini_service import GeminiService
    import asyncio
    
    gemini_service = GeminiService()
    
    if call_status == "ringing":
        return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Welcome to the AI-powered surgical care assistant. Please tell me how you're feeling today.</Say>
    <Gather input="speech dtmf" timeout="15" speechTimeout="5" action="/api/webhooks/twilio/gemini-test" method="POST">
        <Say voice="alice">I'm listening carefully to help you...</Say>
    </Gather>
    <Say voice="alice">I didn't hear anything. Please call back if you need assistance.</Say>
    <Hangup />
</Response>"""
    
    if speech:
        logger.info(f"Processing speech with Gemini: '{speech}'")
        
        try:
            # Create prompt for Gemini
            prompt = f"""You are a caring surgical care assistant. A patient just said: "{speech}"

Please respond as a helpful medical assistant who:
1. Shows empathy and understanding
2. Provides helpful guidance for post-surgical care
3. Asks relevant follow-up questions
4. Keeps responses conversational and under 100 words
5. If they say goodbye/bye, acknowledge and end warmly

Respond naturally as if you're speaking to them directly. Don't use any special formatting."""

            # Get Gemini response with timeout
            try:
                gemini_response = await asyncio.wait_for(
                    gemini_service.generate_response(prompt),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("Gemini API timeout")
                gemini_response = "I'm sorry, I'm having trouble processing that right now. Could you please repeat what you said?"
            
            logger.info(f"Gemini response: {gemini_response[:100]}...")
            
            # Check if user wants to end call
            if any(word in speech.lower() for word in ['goodbye', 'bye', 'end call', 'hang up']):
                return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{gemini_response}</Say>
    <Hangup />
</Response>"""
            
            # Continue conversation
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{gemini_response}</Say>
    <Gather input="speech dtmf" timeout="15" speechTimeout="5" action="/api/webhooks/twilio/gemini-test" method="POST">
        <Say voice="alice">Is there anything else I can help you with?</Say>
    </Gather>
    <Say voice="alice">Thank you for calling. Take care and feel better soon.</Say>
    <Hangup />
</Response>"""
            
        except Exception as e:
            logger.error(f"Gemini processing error: {e}")
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I'm sorry, I'm having technical difficulties. Please call back in a few minutes or contact your healthcare provider directly if this is urgent.</Say>
    <Hangup />
</Response>"""
    
    if digits:
        if digits == "0":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Transferring you to a human representative. Please hold.</Say>
    <Say voice="alice">This is a demo system. In a real implementation, this would transfer to medical staff.</Say>
    <Hangup />
</Response>"""
        
        elif digits == "9":
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for using our surgical care assistant. Take care and get well soon!</Say>
    <Hangup />
</Response>"""
        
        else:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I received your input. Please speak instead so I can better understand and help you. Press 0 for human assistance or 9 to end the call.</Say>
    <Gather input="speech dtmf" timeout="15" speechTimeout="5" action="/api/webhooks/twilio/gemini-test" method="POST">
        <Say voice="alice">Please tell me how you're feeling...</Say>
    </Gather>
    <Hangup />
</Response>"""
    
    # Default response
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! I'm your AI surgical care assistant. Please tell me how you're feeling today or what questions you have about your recovery.</Say>
    <Gather input="speech dtmf" timeout="15" speechTimeout="5" action="/api/webhooks/twilio/gemini-test" method="POST">
        <Say voice="alice">I'm here to help with your post-surgical care...</Say>
    </Gather>
    <Say voice="alice">I didn't hear a response. Please call back if you need assistance.</Say>
    <Hangup />
</Response>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )