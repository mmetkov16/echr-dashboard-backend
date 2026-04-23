"""
Health check and info router
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import HealthCheckResponse
from database import get_db
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
)
async def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        database_connected = True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        database_connected = False

    return HealthCheckResponse(
        status="healthy" if database_connected else "degraded",
        version=settings.API_VERSION,
        database_connected=database_connected,
        message="API is operational" if database_connected else "Database connection failed",
    )


@router.get("/info")
async def api_info():
    """Get API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": "European Court of Human Rights Case Analysis Dashboard API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
