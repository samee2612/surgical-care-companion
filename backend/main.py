"""
TKA Voice Agent - Main FastAPI Application

Entry point for the TKA Voice Agent API server.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    prefix="/webhooks",
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
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    ) 