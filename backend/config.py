"""
Configuration Settings for TKA Voice Agent

Centralized configuration management using Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    PROJECT_NAME: str = "TKA Voice Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/tka_voice"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "tka_voice"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # AI Services
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    WHISPER_MODEL: str = "base"
    TTS_MODEL: str = "tts_models/en/ljspeech/tacotron2-DDC"
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_WEBHOOK_URL: str = ""
    
    # Email/SMS Notifications
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@tka-voice-agent.com"
    
    # Clinical Settings
    DEFAULT_CALL_SCHEDULE: str = "1,3,7,14,30"  # Days post-surgery
    MAX_CALL_DURATION_MINUTES: int = 15
    URGENT_ALERT_THRESHOLD: int = 7  # Pain score threshold
    RESPONSE_TIMEOUT_SECONDS: int = 30
    
    # File Handling
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_AUDIO_FORMATS: List[str] = ["wav", "mp3", "m4a", "flac"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def call_schedule_days(self) -> list[int]:
        """Parse call schedule string into list of integers."""
        return [
            int(day.strip()) 
            for day in self.DEFAULT_CALL_SCHEDULE.split(",")
        ]
    
    @property
    def database_url(self) -> str:
        """Get formatted database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def redis_url(self) -> str:
        """Get formatted Redis URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings."""
    return settings 