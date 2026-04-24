"""
Database configuration and SQLAlchemy models
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Database Setup
# Using StaticPool for SQLite (thread-safe for testing)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Case(Base):
    """
    ECHR Case model representing a case from the European Court of Human Rights
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    
    # ECHR Case Identifiers
    itemid = Column(String(50), unique=True, nullable=False, index=True)  # Unique ECHR ID
    appno = Column(String(50), nullable=False, index=True)  # Application number
    docname = Column(String(255), nullable=True)  # Document name
    
    # Case Details
    country = Column(String(100), nullable=True, index=True)
    article = Column(String(500), nullable=True)  # Violated articles (comma-separated)
    violation = Column(Boolean, default=False)  # Whether violation was found
    violation_count = Column(Integer, default=0)  # Number of violations
    
    # Dates
    judgementdate = Column(DateTime, nullable=True, index=True)
    registration_date = Column(DateTime, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    
    # Status and Outcome
    status = Column(String(50), nullable=True, index=True)  # Final/Pending/Inadmissible
    conclusion = Column(String(255), nullable=True)
    
    # Case Information
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    respondent = Column(String(255), nullable=True)
    applicant = Column(String(255), nullable=True)
    
    # Full Text (optional, can be large)
    full_text = Column(Text, nullable=True)
    
    # Document Links
    pdf_url = Column(String(500), nullable=True)  # URL to case judgment PDF
    
    # Metadata
    language = Column(String(10), default="ENG", nullable=False)
    is_important = Column(Boolean, default=False)
    citation_count = Column(Integer, default=0)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    source = Column(String(100), default="echr-extractor", nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_country_year', 'country', 'judgementdate'),
        Index('idx_article_status', 'article', 'status'),
        Index('idx_violation_date', 'violation', 'judgementdate'),
    )

    class Config:
        from_attributes = True


class ExtractionTask(Base):
    """
    Model to track background extraction tasks
    """
    __tablename__ = "extraction_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, running, completed, failed
    
    # Task Parameters
    count = Column(Integer, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    language = Column(String(10), default="ENG")
    max_items = Column(Integer, nullable=True)
    
    # Results
    cases_extracted = Column(Integer, default=0)
    cases_stored = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    class Config:
        from_attributes = True


def get_db() -> Session:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
