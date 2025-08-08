from fastapi import HTTPException
from app.services.whisperx_service import WhisperXService
from app.services.mock_whisperx_service import MockWhisperXService

whisperx_service = None  # Will be set by main.py

def get_whisperx_service():
    if whisperx_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return whisperx_service