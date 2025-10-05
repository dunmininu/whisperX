"""
WhisperX Cloud Run Microservice - Main Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.mock_whisperx_service import MockWhisperXService
from app.services.whisperx_service import WhisperXService
from app.deps import get_whisperx_service, whisperx_service as global_whisperx_service

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global service instance
whisperx_service: WhisperXService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global whisperx_service

    # Startup
    logger.info("Starting WhisperX Cloud Run Microservice")

    try:
        # Initialize WhisperX service (use mock in development)
        if settings.DEBUG:
            # service = WhisperXService()
            service = MockWhisperXService()
            logger.info("Using Mock WhisperX service for development")
        else:
            service = WhisperXService()
            logger.info("Using real WhisperX service for production")

        await service.initialize()
        logger.info("WhisperX service initialized successfully")

        # Set the global service for dependency injection
        import app.deps
        app.deps.whisperx_service = service

        yield

    except Exception as e:
        logger.error("Failed to initialize WhisperX service", error=str(e))
        raise

    finally:
        # Shutdown
        logger.info("Shutting down WhisperX Cloud Run Microservice")
        if 'service' in locals() and service:
            await service.cleanup()


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="WhisperX Cloud Run Microservice",
        description="Advanced audio transcription and speaker diarization service",
        version="1.0.0",
        docs_url="/docs",
        # docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc",
        # redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "whisperx-microservice",
            "version": "1.0.0",
            "model_loaded": whisperx_service is not None
            and whisperx_service.is_initialized(),
        }

    # Root endpoint
    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint"""
        return {
            "message": "WhisperX Cloud Run Microservice",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
