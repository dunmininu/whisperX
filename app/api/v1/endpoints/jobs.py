"""
Jobs API endpoints for WhisperX Cloud Run Microservice
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.deps import get_whisperx_service
from app.models.database import db_manager
from app.models.schemas import (
    JobListResponse,
    JobRequest,
    JobResponse,
    JobStatus,
    ProcessingStage,
    TranscriptionResult,
)
from app.services.whisperx_service import WhisperXService
from app.utils.auth import verify_api_key
from app.utils.file_utils import save_upload_file, validate_audio_file

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/", response_model=JobResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Create a new transcription job

    This endpoint accepts either:
    1. A direct audio file upload
    2. A URL to an audio file
    """
    try:
        # For now, we'll handle file uploads
        # TODO: Add support for audio URLs
        raise HTTPException(
            status_code=501,
            detail="Direct file upload not implemented yet. Use /upload endpoint.",
        )

    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=JobResponse)
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_size: Optional[str] = Query("large-v2", description="WhisperX model size"),
    enable_diarization: bool = Query(True, description="Enable speaker diarization"),
    enable_alignment: bool = Query(True, description="Enable word-level alignment"),
    language: Optional[str] = Query(
        None, description="Language code (auto-detect if None)"
    ),
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Upload audio file and start transcription job
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Validate file format
        file_extension = Path(file.filename).suffix.lower().lstrip(".")
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {settings.ALLOWED_AUDIO_FORMATS}",
            )

        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024)}MB",
            )

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Save uploaded file
        file_path = await save_upload_file(file, job_id)

        # Validate audio file
        await validate_audio_file(file_path)

        # Save job to database
        job_data = {
            "job_id": job_id,
            "filename": file.filename,
            "model_size": model_size,
            "enable_diarization": enable_diarization,
            "enable_alignment": enable_alignment,
        }
        
        if not db_manager.create_job(job_data):
            raise HTTPException(status_code=500, detail="Failed to create job in database")

        # Create job response
        job_response = JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            audio_file=file.filename,
            model_size=model_size,
            enable_diarization=enable_diarization,
            enable_alignment=enable_alignment,
            progress=0.0,
            current_stage=ProcessingStage.UPLOAD,
        )

        # Add background task for processing
        background_tasks.add_task(
            process_audio_job,
            whisperx_service,
            job_id,
            file_path,
            model_size,
            enable_diarization,
            enable_alignment,
            language,
        )

        logger.info(
            "Job created successfully",
            job_id=job_id,
            filename=file.filename,
            file_size=file.size,
        )

        return job_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create upload job", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Get job status and results
    """
    try:
        # Get job from database
        job = db_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse result_data if it exists
        result_data = None
        if job.get("result_data"):
            try:
                import json
                if isinstance(job["result_data"], str):
                    result_data = json.loads(job["result_data"])
                else:
                    result_data = job["result_data"]
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse result_data for job {job_id}: {str(e)}")
                result_data = None
        
        # Convert database job to response model
        job_response = JobResponse(
            job_id=job["job_id"],
            status=JobStatus(job["status"]),
            created_at=datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00")),
            audio_file=job["filename"],
            model_size=job["model_size"],
            enable_diarization=job["enable_diarization"],
            enable_alignment=job["enable_alignment"],
            progress=1.0 if job["status"] == "completed" else 0.0,
            current_stage=ProcessingStage.COMPLETED if job["status"] == "completed" else ProcessingStage.UPLOAD,
            processing_time=job.get("processing_time"),
            audio_duration=job.get("audio_duration"),
            language=job.get("language"),
            confidence=job.get("confidence"),
            error_message=job.get("error_message"),
            result=result_data,
        )
        
        return job_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Jobs per page"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    List all jobs with pagination and filtering
    """
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get jobs from database
        status_filter = status.value if status else None
        jobs = db_manager.get_jobs(limit=per_page, offset=offset, status=status_filter)
        
        # Get total count for pagination
        all_jobs = db_manager.get_jobs(limit=1000, status=status_filter)  # Get all for count
        total = len(all_jobs)
        
        # Convert database jobs to response models
        job_responses = []
        for job in jobs:
            # Parse result_data if it exists
            result_data = None
            if job.get("result_data"):
                try:
                    import json
                    if isinstance(job["result_data"], str):
                        result_data = json.loads(job["result_data"])
                    else:
                        result_data = job["result_data"]
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse result_data for job {job['job_id']}: {str(e)}")
                    result_data = None
            
            job_response = JobResponse(
                job_id=job["job_id"],
                status=JobStatus(job["status"]),
                created_at=datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00")),
                audio_file=job["filename"],
                model_size=job["model_size"],
                enable_diarization=job["enable_diarization"],
                enable_alignment=job["enable_alignment"],
                progress=1.0 if job["status"] == "completed" else 0.0,
                current_stage=ProcessingStage.COMPLETED if job["status"] == "completed" else ProcessingStage.UPLOAD,
                processing_time=job.get("processing_time"),
                audio_duration=job.get("audio_duration"),
                language=job.get("language"),
                confidence=job.get("confidence"),
                error_message=job.get("error_message"),
                result=result_data,
            )
            job_responses.append(job_response)
        
        # Calculate pagination
        has_next = (page * per_page) < total
        has_prev = page > 1
        
        return JobListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Retry a failed job
    """
    try:
        # Check if job exists
        job = db_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job can be retried
        if job["status"] not in ["failed"]:
            raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
        
        # Reset job status
        db_manager.update_job_status(job_id, "pending")
        
        # Get original file path
        file_path = f"/tmp/whisperx-uploads/{job_id}.mp3"  # Assuming original extension
        
        # Add background task for processing
        background_tasks.add_task(
            process_audio_job,
            whisperx_service,
            job_id,
            file_path,
            job["model_size"],
            job["enable_diarization"],
            job["enable_alignment"],
            job.get("language"),
        )
        
        logger.info("Job retry initiated", job_id=job_id)
        
        # Return updated job response
        job_response = JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.utcnow(),
            audio_file=job["filename"],
            model_size=job["model_size"],
            enable_diarization=job["enable_diarization"],
            enable_alignment=job["enable_alignment"],
            progress=0.0,
            current_stage=ProcessingStage.UPLOAD,
        )
        
        return job_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retry job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Cancel a running job
    """
    try:
        # Check if job exists
        job = db_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job can be cancelled
        if job["status"] in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
        
        # Update job status to cancelled
        if db_manager.update_job_status(job_id, "cancelled"):
            logger.info("Job cancelled successfully", job_id=job_id)
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel job")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_audio_job(
    whisperx_service: WhisperXService,
    job_id: str,
    audio_path: str,
    model_size: str,
    enable_diarization: bool,
    enable_alignment: bool,
    language: Optional[str],
):
    """
    Background task to process audio job
    """
    try:
        logger.info("Starting audio processing", job_id=job_id)
        
        # Update job status to processing
        db_manager.update_job_status(job_id, "processing")
        
        # Record start time for processing time calculation
        import time
        start_time = time.time()

        # Process audio with WhisperX
        try:
            result = await whisperx_service.transcribe_audio(
                audio_path=audio_path,
                language=language or "en"
            )
        except Exception as transcription_error:
            logger.error(f"Transcription failed for job {job_id}: {str(transcription_error)}")
            
            # Try to save any partial results that might exist
            try:
                # Check if there are any cached/partial results
                partial_result = {
                    "text": "Transcription failed",
                    "language": language or "en",
                    "duration": 0.0,
                    "word_segments": [],
                    "speaker_segments": [],
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time,
                    "error": str(transcription_error)
                }
                db_manager.save_job_result(job_id, partial_result)
            except:
                pass
            
            raise transcription_error

        logger.info("Audio processing completed", job_id=job_id)

        # Save result to database
        # Convert the dictionary result to my expected format
        segments = result.get("segments", [])
        
        # Extract text from segments
        full_text = " ".join([seg.get("text", "") for seg in segments])
        
        # Convert to my expected format
        result_dict = {
            "text": full_text,
            "language": result.get("language", "en"),
            "duration": 0.0,  # Will be calculated from segments
            "word_segments": [],
            "speaker_segments": [],
            "confidence": 0.8,  # Default confidence
            "processing_time": 0.0,  # Will be calculated
        }
        
        # Process segments
        for segment in segments:
            # Add speaker segment
            speaker_segment = {
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", ""),
                "speaker": segment.get("speaker", "UNKNOWN"),
            }
            result_dict["speaker_segments"].append(speaker_segment)
            
            # Add word segments
            for word in segment.get("words", []):
                word_segment = {
                    "start": word.get("start", 0),
                    "end": word.get("end", 0),
                    "word": word.get("word", ""),
                    "speaker": word.get("speaker", "UNKNOWN"),
                    "confidence": 0.8,
                }
                result_dict["word_segments"].append(word_segment)
        
        # Calculate duration from segments
        if segments:
            result_dict["duration"] = max(seg.get("end", 0) for seg in segments)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        result_dict["processing_time"] = processing_time
        
        if db_manager.save_job_result(job_id, result_dict):
            logger.info("Job result saved to database", job_id=job_id)
        else:
            logger.error("Failed to save job result to database", job_id=job_id)

    except Exception as e:
        logger.error("Audio processing failed", job_id=job_id, error=str(e))
        
        # Update job status to failed
        db_manager.update_job_status(
            job_id, 
            "failed", 
            error_message=str(e)
        )
