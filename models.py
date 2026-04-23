"""
Pydantic models for API request/response schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    """Base case model with common fields"""
    itemid: str
    appno: str
    docname: Optional[str] = None
    country: Optional[str] = None
    article: Optional[str] = None
    violation: bool = False
    violation_count: int = 0
    judgementdate: Optional[datetime] = None
    registration_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    status: Optional[str] = None
    conclusion: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    respondent: Optional[str] = None
    applicant: Optional[str] = None
    language: str = "ENG"
    is_important: bool = False
    citation_count: int = 0


class CaseCreate(CaseBase):
    """Model for creating a new case"""
    pass


class CaseUpdate(BaseModel):
    """Model for updating an existing case"""
    violation: Optional[bool] = None
    violation_count: Optional[int] = None
    status: Optional[str] = None
    is_important: Optional[bool] = None
    citation_count: Optional[int] = None


class CaseResponse(CaseBase):
    """Model for case response with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime
    source: str = "echr-extractor"
    full_text: Optional[str] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Paginated list of cases"""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CaseResponse]


class ExtractionRequest(BaseModel):
    """Request model for extraction endpoint"""
    count: Optional[int] = Field(None, description="Number of cases to extract")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    language: str = Field("ENG", description="Language code (default: ENG)")
    max_items: Optional[int] = Field(None, description="Maximum items to process")
    fetch_full_text: bool = Field(False, description="Whether to fetch full case text")
    run_background: bool = Field(False, description="Run extraction as background task")


class ExtractionResponse(BaseModel):
    """Response model for extraction endpoint"""
    task_id: str = Field(..., description="Task ID for tracking")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    cases_extracted: int = Field(0, description="Number of cases extracted")
    cases_stored: int = Field(0, description="Number of cases stored in database")
    message: str = Field(..., description="Status message")


class ExtractionTaskResponse(BaseModel):
    """Response for tracking extraction task"""
    task_id: str
    status: str
    cases_extracted: int
    cases_stored: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchExtractionResponse(BaseModel):
    """Response for batch extraction (extract-all-cases)"""
    task_id: str = Field(..., description="Task ID for tracking")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    total_extracted: int = Field(0, description="Total cases extracted")
    total_stored: int = Field(0, description="Total cases stored in database")
    years_completed: List[int] = Field([], description="Years successfully processed")
    years_skipped: List[int] = Field([], description="Years with no new cases")
    years_failed: List[int] = Field([], description="Years that failed to process")
    message: str = Field(..., description="Status message")
    progress_percent: int = Field(0, description="Progress percentage")



class CaseSearchRequest(BaseModel):
    """Request model for case search/filtering"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    country: Optional[str] = Field(None, description="Filter by country code")
    article: Optional[str] = Field(None, description="Filter by article (comma-separated)")
    year: Optional[int] = Field(None, description="Filter by year of judgment")
    year_from: Optional[int] = Field(None, description="Minimum year")
    year_to: Optional[int] = Field(None, description="Maximum year")
    status: Optional[str] = Field(None, description="Filter by case status")
    violation: Optional[bool] = Field(None, description="Filter by violation found")
    search_text: Optional[str] = Field(None, description="Full text search")
    sort_by: Optional[str] = Field("judgementdate", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")


class StatisticsResponse(BaseModel):
    """Response model for statistics endpoint"""
    total_cases: int
    violation_cases: int
    pending_cases: int
    resolved_cases: int
    by_country: dict
    by_year: dict
    by_article: dict
    top_countries: List[tuple]
    top_articles: List[tuple]
    violation_rate: float = Field(..., description="Percentage of cases with violations")


class YearlyTrendResponse(BaseModel):
    """Response model for individual year trend"""
    year: int
    total_cases: int
    violation_cases: int
    cases_per_country: dict


class TrendsResponse(BaseModel):
    """Response model for trends endpoint"""
    trends: List[YearlyTrendResponse]
    yearly_growth: dict = Field(..., description="Year-over-year growth rate")
    total_cases_growth: float = Field(..., description="Overall growth rate")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = "healthy"
    version: str
    database_connected: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
