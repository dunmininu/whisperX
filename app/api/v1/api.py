"""
Main API router for WhisperX Cloud Run Microservice
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs, metrics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
