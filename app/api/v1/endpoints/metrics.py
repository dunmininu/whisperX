"""
Metrics endpoints for WhisperX Cloud Run Microservice
"""

import time
from typing import Any, Dict

import psutil
import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.deps import get_whisperx_service
from app.models.schemas import ServiceMetrics
from app.services.whisperx_service import WhisperXService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/", response_model=ServiceMetrics)
async def get_service_metrics(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Get comprehensive service metrics

    Returns performance statistics, job counts, and system resource usage
    """
    try:
        # Get WhisperX service metrics
        service_metrics = whisperx_service.get_service_metrics()

        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)

        # Calculate average processing time
        total_jobs = service_metrics.get("total_jobs", 0)
        successful_jobs = service_metrics.get("successful_jobs", 0)
        uptime = service_metrics.get("uptime_seconds", 0)

        # Estimate average processing time (this would be better with actual job tracking)
        avg_processing_time = 30.0  # Default estimate in seconds

        # Get GPU usage if available
        gpu_usage_percent = None
        try:
            import torch

            if torch.cuda.is_available():
                gpu_usage_percent = (
                    0.0  # Would need nvidia-ml-py for actual GPU metrics
                )
        except ImportError:
            pass

        return ServiceMetrics(
            total_jobs=total_jobs,
            successful_jobs=successful_jobs,
            failed_jobs=service_metrics.get("failed_jobs", 0),
            average_processing_time=avg_processing_time,
            current_active_jobs=service_metrics.get("active_jobs", 0),
            memory_usage_mb=memory_info.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent,
            gpu_usage_percent=gpu_usage_percent,
        )

    except Exception as e:
        logger.error("Failed to get service metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/performance")
async def get_performance_metrics(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Get detailed performance metrics
    """
    try:
        service_metrics = whisperx_service.get_service_metrics()

        # Calculate performance ratios
        total_jobs = service_metrics.get("total_jobs", 0)
        successful_jobs = service_metrics.get("successful_jobs", 0)
        failed_jobs = service_metrics.get("failed_jobs", 0)

        success_rate = successful_jobs / max(total_jobs, 1)
        failure_rate = failed_jobs / max(total_jobs, 1)

        # Get system performance metrics
        memory_info = psutil.virtual_memory()
        cpu_info = psutil.cpu_percent(interval=1, percpu=True)
        disk_info = psutil.disk_usage("/")

        return {
            "job_metrics": {
                "total_jobs": total_jobs,
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": success_rate,
                "failure_rate": failure_rate,
                "active_jobs": service_metrics.get("active_jobs", 0),
            },
            "system_metrics": {
                "cpu_usage_percent": sum(cpu_info) / len(cpu_info),
                "cpu_cores": len(cpu_info),
                "memory_total_gb": memory_info.total / (1024**3),
                "memory_used_gb": memory_info.used / (1024**3),
                "memory_available_gb": memory_info.available / (1024**3),
                "memory_percent": memory_info.percent,
                "disk_total_gb": disk_info.total / (1024**3),
                "disk_used_gb": disk_info.used / (1024**3),
                "disk_free_gb": disk_info.free / (1024**3),
                "disk_percent": disk_info.percent,
            },
            "service_metrics": {
                "uptime_seconds": service_metrics.get("uptime_seconds", 0),
                "model_size": service_metrics.get("model_size", "unknown"),
                "device": service_metrics.get("device", "cpu"),
                "is_initialized": service_metrics.get("is_initialized", False),
            },
        }

    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve performance metrics"
        )


@router.get("/jobs")
async def get_job_metrics(
    whisperx_service: WhisperXService = Depends(get_whisperx_service),
):
    """
    Get job-specific metrics
    """
    try:
        service_metrics = whisperx_service.get_service_metrics()

        return {
            "job_statistics": {
                "total_jobs": service_metrics.get("total_jobs", 0),
                "successful_jobs": service_metrics.get("successful_jobs", 0),
                "failed_jobs": service_metrics.get("failed_jobs", 0),
                "active_jobs": service_metrics.get("active_jobs", 0),
                "success_rate": service_metrics.get("success_rate", 0.0),
            },
            "processing_info": {
                "model_size": service_metrics.get("model_size", "unknown"),
                "device": service_metrics.get("device", "cpu"),
                "uptime_hours": service_metrics.get("uptime_seconds", 0) / 3600,
            },
        }

    except Exception as e:
        logger.error("Failed to get job metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve job metrics")


@router.get("/system")
async def get_system_metrics():
    """
    Get system resource metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory metrics
        memory_info = psutil.virtual_memory()

        # Disk metrics
        disk_info = psutil.disk_usage("/")

        # Network metrics
        network_info = psutil.net_io_counters()

        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
            },
            "memory": {
                "total_gb": memory_info.total / (1024**3),
                "available_gb": memory_info.available / (1024**3),
                "used_gb": memory_info.used / (1024**3),
                "percent": memory_info.percent,
            },
            "disk": {
                "total_gb": disk_info.total / (1024**3),
                "used_gb": disk_info.used / (1024**3),
                "free_gb": disk_info.free / (1024**3),
                "percent": disk_info.percent,
            },
            "network": {
                "bytes_sent": network_info.bytes_sent,
                "bytes_recv": network_info.bytes_recv,
                "packets_sent": network_info.packets_sent,
                "packets_recv": network_info.packets_recv,
            },
        }

    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")
