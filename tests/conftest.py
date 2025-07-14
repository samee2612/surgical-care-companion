"""
Test configuration and fixtures for TKA Voice Agent
"""
import pytest
import asyncio
import httpx
import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

# Test configuration
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/tka_voice_test")
TEST_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for API testing."""
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0) as client:
        yield client

@pytest.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = redis.from_url(TEST_REDIS_URL)
    yield client
    await client.close()

@pytest.fixture
def test_data():
    """Common test data."""
    return {
        "patient_id": "test_patient_001",
        "call_session_id": "test_session_001",
        "phone_number": "+1234567890",
        "call_type": "followup",
        "transcription": "I'm feeling much better today. Pain level is about 3 out of 10."
    }
