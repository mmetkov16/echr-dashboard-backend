"""
Cases router - handles case listing, searching, and filtering
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from models import CaseListResponse, CaseResponse, CaseSearchRequest, ErrorResponse
from database import get_db, Case
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["cases"])


@router.get(
    "/cases",
    response_model=CaseListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
    },
)
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    country: Optional[str] = Query(None, description="Filter by country"),
    article: Optional[str] = Query(None, description="Filter by article"),
    year: Optional[int] = Query(None, description="Filter by year"),
    year_from: Optional[int] = Query(None, description="Start year"),
    year_to: Optional[int] = Query(None, description="End year"),
    status: Optional[str] = Query(None, description="Filter by status"),
    violation: Optional[bool] = Query(None, description="Filter by violation"),
    search_text: Optional[str] = Query(None, description="Search text"),
    sort_by: str = Query("judgementdate", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
) -> CaseListResponse:
    """
    List cases with filtering and pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
    - country: Country code filter
    - article: Article number filter (partial match)
    - year: Exact year filter
    - year_from/year_to: Year range filter
    - status: Case status filter
    - violation: Filter by violation (true/false/null)
    - search_text: Full text search
    - sort_by: Field to sort by (judgementdate, country, etc.)
    - sort_order: asc or desc
    """
    try:
        # Build filters
        filters = []

        if country:
            filters.append(Case.country.ilike(f"%{country}%"))

        if article:
            filters.append(Case.article.ilike(f"%{article}%"))

        if year:
            filters.append(
                and_(
                    Case.judgementdate >= f"{year}-01-01",
                    Case.judgementdate <= f"{year}-12-31",
                )
            )
        else:
            if year_from:
                filters.append(Case.judgementdate >= f"{year_from}-01-01")
            if year_to:
                filters.append(Case.judgementdate <= f"{year_to}-12-31")

        if status:
            filters.append(Case.status.ilike(f"%{status}%"))

        if violation is not None:
            filters.append(Case.violation == violation)

        if search_text:
            filters.append(
                or_(
                    Case.title.ilike(f"%{search_text}%"),
                    Case.description.ilike(f"%{search_text}%"),
                    Case.full_text.ilike(f"%{search_text}%"),
                )
            )

        # Build query
        query = db.query(Case)

        if filters:
            query = query.filter(and_(*filters))

        # Count total
        total = query.count()

        # Sort
        sort_column = getattr(Case, sort_by, Case.judgementdate)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Paginate
        skip = (page - 1) * page_size
        cases = query.offset(skip).limit(page_size).all()

        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size

        return CaseListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[CaseResponse.from_orm(case) for case in cases],
        )

    except ValueError as e:
        logger.warning(f"Invalid filter parameter: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing cases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Get a specific case by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    return CaseResponse.from_orm(case)


@router.get(
    "/cases/search/{itemid}",
    response_model=CaseResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def search_case_by_itemid(
    itemid: str,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Search for a case by ECHR item ID"""
    case = db.query(Case).filter(Case.itemid == itemid).first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {itemid} not found")

    return CaseResponse.from_orm(case)


@router.get(
    "/cases/appno/{appno}",
    response_model=CaseListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
    },
)
async def search_by_appno(
    appno: str,
    db: Session = Depends(get_db),
) -> CaseListResponse:
    """Search for cases by application number (partial match)"""
    try:
        query = db.query(Case).filter(Case.appno.ilike(f"%{appno}%"))
        total = query.count()
        cases = query.limit(100).all()  # Limit results

        return CaseListResponse(
            total=total,
            page=1,
            page_size=100,
            total_pages=1 if total <= 100 else (total + 99) // 100,
            items=[CaseResponse.from_orm(case) for case in cases],
        )

    except Exception as e:
        logger.error(f"Error searching by appno: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
