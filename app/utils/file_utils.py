"""
File utility functions for WhisperX Cloud Run Microservice
"""

import os
from pathlib import Path
from typing import Optional

import aiofiles
import structlog
from fastapi import HTTPException, UploadFile

from app.core.config import settings

logger = structlog.get_logger(__name__)


async def save_upload_file(upload_file: UploadFile, job_id: str) -> str:
    """
    Save uploaded file to temporary directory

    Args:
        upload_file: Uploaded file
        job_id: Job identifier for file naming

    Returns:
        Path to saved file
    """
    try:
        # Use /tmp directory for Cloud Run compatibility
        # In development, use settings.UPLOADS_DIR, in production use /tmp
        if os.path.exists("/tmp") and os.access("/tmp", os.W_OK):
            uploads_dir = Path("/tmp/whisperx-uploads")
        else:
            uploads_dir = Path(settings.UPLOADS_DIR)
        
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Generate file path
        file_extension = Path(upload_file.filename).suffix
        file_path = uploads_dir / f"{job_id}{file_extension}"

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            content = await upload_file.read()
            await f.write(content)

        logger.info(
            "File saved successfully",
            job_id=job_id,
            filename=upload_file.filename,
            file_size=len(content),
            file_path=str(file_path),
        )

        return str(file_path)

    except Exception as e:
        logger.error(
            "Failed to save uploaded file",
            job_id=job_id,
            filename=upload_file.filename,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded file: {str(e)}"
        )


async def validate_audio_file(file_path: str) -> bool:
    """
    Validate audio file format and integrity

    Args:
        file_path: Path to audio file

    Returns:
        True if file is valid

    Raises:
        HTTPException: If file is invalid
    """
    try:
        from pydub import AudioSegment

        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError("File does not exist")

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("File is empty")

        if file_size > settings.MAX_FILE_SIZE:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum ({settings.MAX_FILE_SIZE} bytes)"
            )

        # Try to load audio file
        audio = AudioSegment.from_file(file_path)

        # Check audio duration
        duration_seconds = len(audio) / 1000.0
        if duration_seconds > settings.MAX_AUDIO_DURATION:
            raise ValueError(
                f"Audio duration ({duration_seconds}s) exceeds maximum ({settings.MAX_AUDIO_DURATION}s)"
            )

        # Check if audio has content
        if len(audio) == 0:
            raise ValueError("Audio file has no content")

        logger.info(
            "Audio file validated successfully",
            file_path=file_path,
            duration_seconds=duration_seconds,
            file_size=file_size,
        )

        return True

    except Exception as e:
        logger.error("Audio file validation failed", file_path=file_path, error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower().lstrip(".")


def is_valid_audio_format(filename: str) -> bool:
    """Check if file has valid audio format"""
    extension = get_file_extension(filename)
    return extension in settings.ALLOWED_AUDIO_FORMATS


async def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up temporary file

    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug("Temporary file cleaned up", file_path=file_path)
    except Exception as e:
        logger.warning(
            "Failed to cleanup temporary file", file_path=file_path, error=str(e)
        )


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    if not os.path.exists(file_path):
        return 0.0

    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)
