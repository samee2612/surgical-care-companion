# surgicalcompanian/backend/main.py
"""
TKA Voice Agent - Main FastAPI Application

Entry point for the TKA Voice Agent API server.
"""

from fastapi import FastAPI, Depends, Request 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path
import os # Added for os.getenv in startup

# Ensure backend root is in Python path for imports like 'backend.services'
sys.path.append(str(Path(__file__).parent.parent))

# Import shared services from the new common services location
from backend.services.database_manager import DatabaseManager
from backend.services.llm_client import LLMClient
from backend.services.orchestrator import ConversationOrchestrator
from backend.services.prompt_generator import PromptGenerator

# Import configuration settings
from backend.config import settings

# Import API routers (voice_chat will now contain the core logic)
from backend.api.patients import router as patients_router
from backend.api.voice_chat import router as voice_chat_router
# from backend.api.calls import router as calls_router # Uncomment if you have this
# from backend.api.clinical import router as clinical_router # Uncomment if you have this
# from backend.api.webhooks import router as webhooks_router # Uncomment if you have this

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

# --- Global Instances (Initialized ONCE at Application Startup) ---
# These instances will be shared across all requests
db_manager: DatabaseManager = None
llm_client: LLMClient = None
prompt_generator: PromptGenerator = None
orchestrator: ConversationOrchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize application services on startup."""
    global db_manager, llm_client, prompt_generator, orchestrator

    logger.info("Starting TKA Voice Agent API...")
    
    # Initialize Database Manager
    try:
        db_manager = DatabaseManager()
        # Optional: Test DB connection here
        # For simple test: db_manager._get_connection().close()
        logger.info("DatabaseManager initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize DatabaseManager: {e}")
        raise # Critical failure, stop startup

    # Initialize LLM Client
    try:
        # GEMINI_API_KEY must be in environment (from Docker Compose)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set. LLM client cannot be initialized.")
            raise ValueError("GEMINI_API_KEY is missing.")
        llm_client = LLMClient(api_key)
        logger.info("LLMClient initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize LLMClient: {e}")
        raise # Critical failure, stop startup

    # Initialize Prompt Generator
    prompt_generator = PromptGenerator()
    logger.info("PromptGenerator initialized successfully.")

    # Initialize Conversation Orchestrator
    # Pass dependencies to orchestrator if it needs them directly, or rely on global access
    # Currently, orchestrator creates its own LLMClient and PromptGenerator.
    # To use the global instances: orchestrator = ConversationOrchestrator(llm_client, prompt_generator)
    # But current orchestrator code doesn't take them in init. So stick with its current __init__
    orchestrator = ConversationOrchestrator() # It still uses os.getenv internally
    logger.info("ConversationOrchestrator initialized successfully.")

    # Create database tables (if using SQLAlchemy migrations are better)
    # The database_schema.sql via docker-entrypoint-initdb.d/init.sql is primary for tables
    # create_tables() # This line is removed as per the edit hint from the file
    logger.info("Database tables assumed to be initialized by Docker Compose or migrations.")

    logger.info("TKA Voice Agent API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down TKA Voice Agent API...")
    # Add any cleanup like closing DB connections if using a pool (not direct conn per request)


# Include API routers
app.include_router(
    patients_router,
    prefix=f"{settings.API_V1_STR}/patients",
    tags=["patients"]
)

# This router now includes your combined Flask-like logic
app.include_router(
    voice_chat_router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["voice-chat"]
)

# Add other API routers if you uncommented them in your actual main.py
# app.include_router(calls_router, prefix=f"{settings.API_V1_STR}/calls", tags=["calls"])
# app.include_router(clinical_router, prefix=f"{settings.API_V1_STR}/clinical", tags=["clinical"])
# app.include_router(webhooks_router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TKA Voice Agent API",
        "version": settings.VERSION,
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat() # Use current datetime
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception): # Type hints for clarity
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True) # exc_info=True to log traceback
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    # This block runs if main.py is executed directly (e.g., `python main.py`)
    # For Docker Compose, the CMD in Dockerfile runs uvicorn directly.
    uvicorn.run(
        "backend.main:app", # Correct path for uvicorn when run from project root
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD, # Use settings for reload
        log_level=settings.LOG_LEVEL.lower()
    )