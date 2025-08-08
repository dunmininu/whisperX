"""
Structured logging configuration for WhisperX Cloud Run Microservice
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging() -> None:
    """Setup structured logging configuration"""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class RequestLogger:
    """Request logging middleware"""

    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger

    def log_request(self, request_id: str, method: str, path: str, **kwargs) -> None:
        """Log incoming request"""
        self.logger.info(
            "Incoming request",
            request_id=request_id,
            method=method,
            path=path,
            **kwargs,
        )

    def log_response(
        self, request_id: str, status_code: int, duration: float, **kwargs
    ) -> None:
        """Log response"""
        self.logger.info(
            "Response sent",
            request_id=request_id,
            status_code=status_code,
            duration_ms=duration * 1000,
            **kwargs,
        )

    def log_error(self, request_id: str, error: Exception, **kwargs) -> None:
        """Log error"""
        self.logger.error(
            "Request error",
            request_id=request_id,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs,
        )


class ProcessingLogger:
    """Processing task logging"""

    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger

    def log_job_start(self, job_id: str, audio_file: str, **kwargs) -> None:
        """Log job start"""
        self.logger.info("Job started", job_id=job_id, audio_file=audio_file, **kwargs)

    def log_job_progress(
        self, job_id: str, stage: str, progress: float, **kwargs
    ) -> None:
        """Log job progress"""
        self.logger.info(
            "Job progress", job_id=job_id, stage=stage, progress=progress, **kwargs
        )

    def log_job_complete(self, job_id: str, duration: float, **kwargs) -> None:
        """Log job completion"""
        self.logger.info(
            "Job completed", job_id=job_id, duration_seconds=duration, **kwargs
        )

    def log_job_error(self, job_id: str, error: Exception, **kwargs) -> None:
        """Log job error"""
        self.logger.error(
            "Job failed",
            job_id=job_id,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs,
        )


class WhisperXLogger:
    """WhisperX-specific logging"""

    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger

    def log_model_load(self, model_size: str, device: str, **kwargs) -> None:
        """Log model loading"""
        self.logger.info(
            "WhisperX model loaded", model_size=model_size, device=device, **kwargs
        )

    def log_transcription_start(
        self, audio_file: str, model_size: str, **kwargs
    ) -> None:
        """Log transcription start"""
        self.logger.info(
            "Transcription started",
            audio_file=audio_file,
            model_size=model_size,
            **kwargs,
        )

    def log_transcription_complete(
        self, audio_file: str, duration: float, **kwargs
    ) -> None:
        """Log transcription completion"""
        self.logger.info(
            "Transcription completed",
            audio_file=audio_file,
            duration_seconds=duration,
            **kwargs,
        )

    def log_diarization_start(self, audio_file: str, **kwargs) -> None:
        """Log diarization start"""
        self.logger.info("Diarization started", audio_file=audio_file, **kwargs)

    def log_diarization_complete(
        self, audio_file: str, speaker_count: int, **kwargs
    ) -> None:
        """Log diarization completion"""
        self.logger.info(
            "Diarization completed",
            audio_file=audio_file,
            speaker_count=speaker_count,
            **kwargs,
        )
