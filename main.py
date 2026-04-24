"""
ECHR Dashboard FastAPI Application
Main entry point for the backend API
"""
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import get_settings
from database import init_db, get_db
from models import ErrorResponse

# Import routers
from routers import extraction, cases, statistics, health

# Configuration
settings = get_settings()

# Setup logging
logging_config: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": "echr_dashboard.log",
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
        },
        "sqlalchemy": {
            "level": "WARNING",
        },
    },
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting ECHR Dashboard API")
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # Auto-populate database if empty (for Railway deployment)
        from database import Case, SessionLocal
        db = SessionLocal()
        case_count = db.query(Case).count()
        db.close()
        
        if case_count == 0:
            logger.info("Database is empty. Auto-populating with ECHR cases...")
            try:
                from batch_insert_cases import insert_cases_for_year
                total = 0
                for year in range(1990, 2027):
                    logger.info(f"Inserting cases for year {year}...")
                    inserted = insert_cases_for_year(year)
                    total += inserted
                logger.info(f"Successfully populated database with {total} cases")
            except Exception as e:
                logger.error(f"Failed to auto-populate database: {e}")
                logger.warning("Continuing startup without data. Manual population required.")
        else:
            logger.info(f"Database already contains {case_count} cases")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ECHR Dashboard API")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description="European Court of Human Rights Case Analysis Dashboard API",
    version=settings.API_VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": "HTTP_ERROR",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation Error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        },
    )


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and outgoing responses"""
    logger.debug(f"{request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.debug(f"{request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
        raise


# Include routers
app.include_router(health.router)
app.include_router(extraction.router)
app.include_router(cases.router)
app.include_router(statistics.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Handle startup events"""
    logger.info(f"API started - {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Database: {settings.DATABASE_URL}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Handle shutdown events"""
    logger.info(f"API shutdown - {settings.API_TITLE}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
