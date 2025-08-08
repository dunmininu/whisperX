"""
Health check endpoints for WhisperX Cloud Run Microservice
"""

import time
from typing import Any, Dict

import psutil
import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.deps import get_whisperx_service
from app.models.schemas import HealthResponse
from app.services.whisperx_service import WhisperXService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/", response_model=HealthResponse)
async def health_check(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Health check endpoint

    Returns service status, model loading status, and system metrics
    """
    try:
        # Get service metrics
        metrics = whisperx_service.get_service_metrics()

        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)

        # Check GPU availability
        gpu_available = False
        try:
            import torch

            gpu_available = torch.cuda.is_available()
        except ImportError:
            pass

        # Calculate uptime
        uptime = metrics.get("uptime_seconds", 0)

        return HealthResponse(
            status="healthy" if whisperx_service.is_initialized() else "unhealthy",
            service="whisperx-microservice",
            version=settings.VERSION,
            model_loaded=whisperx_service.is_initialized(),
            uptime=uptime,
            memory_usage={
                "total_mb": memory_info.total / (1024 * 1024),
                "available_mb": memory_info.available / (1024 * 1024),
                "used_mb": memory_info.used / (1024 * 1024),
                "percent": memory_info.percent,
            },
            gpu_available=gpu_available,
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/ready")
async def readiness_check(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Readiness check endpoint

    Used by Kubernetes/Cloud Run to determine if service is ready to receive traffic
    """
    try:
        if not whisperx_service.is_initialized():
            raise HTTPException(status_code=503, detail="Service not ready")

        return {"status": "ready"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint

    Used by Kubernetes/Cloud Run to determine if service is alive
    """
    try:
        return {"status": "alive"}

    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not alive")


@router.get("/detailed")
async def detailed_health_check(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Detailed health check with comprehensive system information
    """
    try:
        # Get basic health info
        basic_health = await health_check(whisperx_service)

        # Get detailed system info
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage": psutil.disk_usage("/").percent,
            "load_average": (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
            ),
        }

        # Get WhisperX service metrics
        service_metrics = whisperx_service.get_service_metrics()

        return {
            "health": basic_health.dict(),
            "system": system_info,
            "service": service_metrics,
            "config": {
                "model_size": settings.MODEL_SIZE,
                "max_audio_duration": settings.MAX_AUDIO_DURATION,
                "enable_gpu": settings.ENABLE_GPU,
                "compute_type": settings.COMPUTE_TYPE,
                "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
                "allowed_formats": settings.ALLOWED_AUDIO_FORMATS,
            },
        }

    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")
