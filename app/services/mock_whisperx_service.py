"""
Mock WhisperX service for development without heavy ML dependencies
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import structlog

from app.core.config import settings
from app.models.schemas import (
    ProcessingStage,
    SpeakerSegment,
    TranscriptionResult,
    WordSegment,
)


class MockWhisperXService:
    """Mock WhisperX service for development"""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.is_initialized = False
        self.processing_jobs: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.total_jobs = 0
        self.successful_jobs = 0
        self.failed_jobs = 0

    async def initialize(self) -> None:
        """Initialize mock service"""
        self.logger.info("Initializing Mock WhisperX service")
        await asyncio.sleep(1)  # Simulate initialization time
        self.is_initialized = True
        self.logger.info("Mock WhisperX service initialized successfully")

    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self.is_initialized

    async def cleanup(self) -> None:
        """Cleanup mock service"""
        self.logger.info("Mock WhisperX service cleaned up")
        self.is_initialized = False

    async def process_audio(
        self,
        audio_path: str,
        job_id: str,
        enable_diarization: bool = True,
        enable_alignment: bool = True,
        language: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> TranscriptionResult:
        """
        Mock audio processing
        """
        if not self.is_initialized:
            raise RuntimeError("Mock WhisperX service not initialized")

        start_time = time.time()
        self.total_jobs += 1

        try:
            # Simulate processing stages
            stages = [
                (0.1, "Loading audio file"),
                (0.2, "Starting transcription"),
                (0.6, "Transcription completed"),
                (0.7, "Aligning timestamps"),
                (0.8, "Alignment completed"),
                (0.85, "Performing speaker diarization"),
                (0.95, "Diarization completed"),
                (1.0, "Processing completed"),
            ]

            for progress, stage in stages:
                if progress_callback:
                    progress_callback(progress, stage)
                await asyncio.sleep(0.5)  # Simulate processing time

            # Create mock result
            mock_text = "Hello, this is a mock transcription from the WhisperX service. This demonstrates the capabilities of my audio processing pipeline."

            word_segments = [
                WordSegment(
                    word="Hello",
                    start=0.0,
                    end=0.5,
                    speaker="SPEAKER_00",
                    confidence=0.95,
                ),
                WordSegment(
                    word="this",
                    start=0.5,
                    end=1.0,
                    speaker="SPEAKER_00",
                    confidence=0.92,
                ),
                WordSegment(
                    word="is", start=1.0, end=1.3, speaker="SPEAKER_00", confidence=0.89
                ),
                WordSegment(
                    word="a", start=1.3, end=1.4, speaker="SPEAKER_00", confidence=0.91
                ),
                WordSegment(
                    word="mock",
                    start=1.4,
                    end=1.8,
                    speaker="SPEAKER_00",
                    confidence=0.88,
                ),
            ]

            speaker_segments = [
                SpeakerSegment(speaker="SPEAKER_00", start=0.0, end=5.0, text=mock_text)
            ]

            processing_time = time.time() - start_time

            result = TranscriptionResult(
                text=mock_text,
                language="en",
                duration=5.0,
                word_segments=word_segments,
                speaker_segments=speaker_segments,
                confidence=0.91,
                processing_time=processing_time,
            )

            self.successful_jobs += 1
            self.logger.info(
                "Mock audio processing completed",
                job_id=job_id,
                audio_path=audio_path,
                processing_time=processing_time,
            )

            return result

        except Exception as e:
            self.failed_jobs += 1
            self.logger.error(
                "Mock audio processing failed",
                job_id=job_id,
                audio_path=audio_path,
                error=str(e),
            )
            raise

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get mock service metrics"""
        uptime = time.time() - self.start_time

        return {
            "total_jobs": self.total_jobs,
            "successful_jobs": self.successful_jobs,
            "failed_jobs": self.failed_jobs,
            "success_rate": self.successful_jobs / max(self.total_jobs, 1),
            "uptime_seconds": uptime,
            "model_size": "mock-large-v2",
            "device": "cpu",
            "is_initialized": self.is_initialized,
            "active_jobs": len(self.processing_jobs),
        }
