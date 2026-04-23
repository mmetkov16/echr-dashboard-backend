"""
Configuration management for ECHR Dashboard API
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    API_TITLE: str = "ECHR Dashboard API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./echr_dashboard.db"  # Default to SQLite for simplicity
    SQLALCHEMY_ECHO: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: list = ["*"]
    
    # ECHR Extractor Configuration
    ECHR_MAX_RETRIES: int = 3
    ECHR_TIMEOUT: int = 30
    ECHR_DEFAULT_LANGUAGE: str = "ENG"
    
    # Background Task Configuration
    BACKGROUND_TASKS_ENABLED: bool = True
    TASK_QUEUE_MAX_SIZE: int = 100
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
