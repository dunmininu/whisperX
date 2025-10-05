"""
Pydantic schemas for WhisperX Cloud Run Microservice
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(str, Enum):
    """Processing stage enumeration"""

    UPLOAD = "upload"
    TRANSCRIPTION = "transcription"
    DIARIZATION = "diarization"
    ALIGNMENT = "alignment"
    COMPLETED = "completed"


class AudioFormat(str, Enum):
    """Supported audio formats"""

    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"


class ModelSize(str, Enum):
    """WhisperX model sizes"""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"


class WordSegment(BaseModel):
    """Word-level segment model"""

    word: str = Field(..., description="Word text")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    speaker: Optional[str] = Field("UNKNOWN", description="Speaker identifier")
    confidence: Optional[float] = Field(0.8, description="Confidence score")


class SpeakerSegment(BaseModel):
    """Speaker segment model"""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    speaker: str = Field("UNKNOWN", description="Speaker identifier")
    words: Optional[List[WordSegment]] = Field(default=[], description="Word-level segments in this speaker segment")


class TranscriptionResult(BaseModel):
    """Transcription result model"""

    text: str = Field(..., description="Full transcribed text")
    language: str = Field(..., description="Detected language")
    duration: float = Field(..., description="Audio duration in seconds")
    word_segments: List[WordSegment] = Field(
        default=[], description="Word-level segments"
    )
    speaker_segments: List[SpeakerSegment] = Field(
        default=[], description="Speaker segments"
    )
    confidence: float = Field(0.8, description="Overall confidence score")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class JobRequest(BaseModel):
    """Job request model"""

    audio_url: Optional[str] = Field(None, description="URL to audio file")
    audio_file: Optional[str] = Field(None, description="Local audio file path")
    model_size: ModelSize = Field(
        default=ModelSize.LARGE_V2, description="WhisperX model size"
    )
    enable_diarization: bool = Field(
        default=True, description="Enable speaker diarization"
    )
    enable_alignment: bool = Field(
        default=True, description="Enable word-level alignment"
    )
    language: Optional[str] = Field(
        None, description="Language code (auto-detect if None)"
    )
    compute_type: str = Field(
        default="float16", description="Compute type for processing"
    )

    @validator("audio_url", "audio_file")
    def validate_audio_source(cls, v, values):
        """Ensure either audio_url or audio_file is provided"""
        if not values.get("audio_url") and not values.get("audio_file"):
            raise ValueError("Either audio_url or audio_file must be provided")
        return v


class JobResponse(BaseModel):
    """Job response model"""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    audio_file: str = Field(..., description="Audio file path or URL")
    model_size: ModelSize = Field(..., description="WhisperX model size")
    enable_diarization: bool = Field(..., description="Diarization enabled")
    enable_alignment: bool = Field(..., description="Alignment enabled")
    progress: float = Field(default=0.0, description="Processing progress (0-1)")
    current_stage: Optional[ProcessingStage] = Field(
        None, description="Current processing stage"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result: Optional[TranscriptionResult] = Field(None, description="Processing result")


class JobListResponse(BaseModel):
    """Job list response model"""

    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Jobs per page")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    model_loaded: bool = Field(..., description="WhisperX model loaded")
    uptime: float = Field(..., description="Service uptime in seconds")
    memory_usage: Optional[Dict[str, Any]] = Field(
        None, description="Memory usage statistics"
    )
    gpu_available: bool = Field(..., description="GPU availability")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class ProcessingOptions(BaseModel):
    """Processing options model"""

    model_size: ModelSize = Field(
        default=ModelSize.LARGE_V2, description="WhisperX model size"
    )
    enable_diarization: bool = Field(
        default=True, description="Enable speaker diarization"
    )
    enable_alignment: bool = Field(
        default=True, description="Enable word-level alignment"
    )
    language: Optional[str] = Field(None, description="Language code")
    compute_type: str = Field(default="float16", description="Compute type")
    batch_size: int = Field(default=16, description="Batch size for processing")
    max_audio_duration: int = Field(
        default=300, description="Maximum audio duration in seconds"
    )


class ServiceMetrics(BaseModel):
    """Service metrics model"""

    total_jobs: int = Field(..., description="Total jobs processed")
    successful_jobs: int = Field(..., description="Successfully completed jobs")
    failed_jobs: int = Field(..., description="Failed jobs")
    average_processing_time: float = Field(
        ..., description="Average processing time in seconds"
    )
    current_active_jobs: int = Field(..., description="Currently active jobs")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    gpu_usage_percent: Optional[float] = Field(None, description="GPU usage percentage")
