"""
Pytest configuration and fixtures for WhisperX Cloud Run Microservice
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_application
from app.services.whisperx_service import WhisperXService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI application for testing."""
    return create_application()


@pytest.fixture
def client(app: FastAPI) -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_whisperx_service() -> Mock:
    """Create a mock WhisperX service for testing."""
    mock_service = Mock(spec=WhisperXService)
    mock_service.is_initialized.return_value = True
    mock_service.get_service_metrics.return_value = {
        "total_jobs": 10,
        "successful_jobs": 8,
        "failed_jobs": 2,
        "success_rate": 0.8,
        "uptime_seconds": 3600,
        "model_size": "large-v2",
        "device": "cpu",
        "is_initialized": True,
        "active_jobs": 1,
    }
    return mock_service


@pytest.fixture
def sample_audio_file() -> str:
    """Create a sample audio file path for testing."""
    return "tests/fixtures/sample_audio.wav"


@pytest.fixture
def sample_job_request() -> dict:
    """Create a sample job request for testing."""
    return {
        "audio_file": "sample_audio.mp3",
        "model_size": "large-v2",
        "enable_diarization": True,
        "enable_alignment": True,
        "language": "en",
    }


@pytest.fixture
def sample_transcription_result() -> dict:
    """Create a sample transcription result for testing."""
    return {
        "text": "Hello, this is a test transcription.",
        "language": "en",
        "duration": 5.0,
        "word_segments": [
            {
                "word": "Hello",
                "start": 0.0,
                "end": 0.5,
                "speaker": "SPEAKER_00",
                "confidence": 0.95,
            },
            {
                "word": "this",
                "start": 0.5,
                "end": 1.0,
                "speaker": "SPEAKER_00",
                "confidence": 0.92,
            },
        ],
        "speaker_segments": [
            {
                "speaker": "SPEAKER_00",
                "start": 0.0,
                "end": 2.0,
                "text": "Hello, this is",
            }
        ],
        "confidence": 0.93,
        "processing_time": 2.5,
    }


@pytest.fixture
def mock_api_key() -> str:
    """Create a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def test_settings():
    """Create test settings."""
    from app.core.config import Settings

    class TestSettings(Settings):
        GOOGLE_CLOUD_PROJECT = "test-project"
        CLOUD_STORAGE_BUCKET = "test-bucket"
        API_KEYS = ["test-api-key-12345"]
        DEBUG = True
        LOG_LEVEL = "DEBUG"

    return TestSettings()


@pytest.fixture(autouse=True)
def setup_test_environment(test_settings, monkeypatch):
    """Setup test environment with mocked settings."""
    # Mock environment variables
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("CLOUD_STORAGE_BUCKET", "test-bucket")
    monkeypatch.setenv("API_KEYS", "test-api-key-12345")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Mock settings
    monkeypatch.setattr("app.core.config.settings", test_settings)


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator:
    """Create an async test client."""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
