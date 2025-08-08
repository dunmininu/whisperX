"""
Authentication utilities for WhisperX Cloud Run Microservice
"""

from typing import Optional

import structlog
from fastapi import Header, HTTPException

from app.core.config import settings

logger = structlog.get_logger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """
    Verify API key from request header

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Verified API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Skip API key verification if no keys are configured
    if not settings.API_KEYS:
        return "no_auth_required"

    if not x_api_key:
        logger.warning("Missing API key")
        raise HTTPException(status_code=401, detail="API key required")

    if x_api_key not in settings.API_KEYS:
        logger.warning("Invalid API key", api_key=x_api_key[:8] + "...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.debug("API key verified", api_key=x_api_key[:8] + "...")
    return x_api_key


def get_api_key_header() -> str:
    """Get the API key header name"""
    return settings.API_KEY_HEADER
