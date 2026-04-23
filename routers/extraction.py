"""
Extraction router - handles ECHR data extraction
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from models import ExtractionRequest, ExtractionResponse, ExtractionTaskResponse, ErrorResponse, BatchExtractionResponse
from database import get_db, Case, ExtractionTask
from config import get_settings
from echr_service import extract_echr_cases, batch_extract_all_cases

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["extraction"])

# In-memory storage for task tracking (in production, use Redis or database)
extraction_tasks = {}


async def background_extraction(
    task_id: str,
    count: Optional[int],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    language: str,
    max_items: Optional[int],
    fetch_full_text: bool,
    db: Session,
) -> None:
    """Background task for extracting ECHR cases"""
    try:
        # Update task status
        task = db.query(ExtractionTask).filter(
            ExtractionTask.task_id == task_id
        ).first()
        if task:
            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()

        # Extract cases from ECHR
        cases = await extract_echr_cases(
            count=count,
            start_date=start_date,
            end_date=end_date,
            language=language,
            max_items=max_items,
            fetch_full_text=fetch_full_text,
        )

        # Store cases in database
        stored_count = 0
        for case_data in cases:
            try:
                # Check if case already exists
                existing = db.query(Case).filter(
                    Case.itemid == case_data.get("itemid")
                ).first()

                if not existing:
                    case = Case(**case_data)
                    db.add(case)
                    stored_count += 1
                else:
                    # Update existing case
                    for key, value in case_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    stored_count += 1

            except Exception as e:
                logger.error(f"Error storing case {case_data.get('itemid')}: {e}")

        db.commit()

        # Update task completion
        if task:
            task.status = "completed"
            task.cases_extracted = len(cases)
            task.cases_stored = stored_count
            task.completed_at = datetime.utcnow()
            db.commit()

        logger.info(
            f"Task {task_id} completed: extracted {len(cases)}, stored {stored_count}"
        )

    except Exception as e:
        logger.error(f"Error in background extraction task {task_id}: {e}")
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()


@router.post(
    "/extract-cases",
    response_model=ExtractionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def extract_cases(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ExtractionResponse:
    """
    Extract ECHR cases and store in database
    
    Parameters:
    - count: Number of cases to extract
    - start_date: Filter from date
    - end_date: Filter to date
    - language: Language code (default: ENG)
    - max_items: Maximum items to process
    - fetch_full_text: Whether to fetch full text (slower)
    - run_background: Run as background task
    """
    try:
        # Validate request
        if not request.count and not request.start_date and not request.end_date:
            raise HTTPException(
                status_code=400,
                detail="At least one of: count, start_date, or end_date must be provided",
            )

        task_id = str(uuid.uuid4())

        # Create task record
        extraction_task = ExtractionTask(
            task_id=task_id,
            status="pending" if request.run_background else "running",
            count=request.count,
            start_date=request.start_date,
            end_date=request.end_date,
            language=request.language,
            max_items=request.max_items,
        )
        db.add(extraction_task)
        db.commit()

        if request.run_background:
            # Add to background tasks
            background_tasks.add_task(
                background_extraction,
                task_id=task_id,
                count=request.count,
                start_date=request.start_date,
                end_date=request.end_date,
                language=request.language,
                max_items=request.max_items,
                fetch_full_text=request.fetch_full_text,
                db=db,
            )
            return ExtractionResponse(
                task_id=task_id,
                status="pending",
                cases_extracted=0,
                cases_stored=0,
                message="Extraction started in background. Use GET /task/{task_id} to check progress.",
            )
        else:
            # Synchronous extraction
            cases = await extract_echr_cases(
                count=request.count,
                start_date=request.start_date,
                end_date=request.end_date,
                language=request.language,
                max_items=request.max_items,
                fetch_full_text=request.fetch_full_text,
            )

            stored_count = 0
            for case_data in cases:
                try:
                    existing = db.query(Case).filter(
                        Case.itemid == case_data.get("itemid")
                    ).first()

                    if not existing:
                        case = Case(**case_data)
                        db.add(case)
                        stored_count += 1

                except Exception as e:
                    logger.error(f"Error storing case: {e}")

            db.commit()

            # Update task
            extraction_task.status = "completed"
            extraction_task.cases_extracted = len(cases)
            extraction_task.cases_stored = stored_count
            extraction_task.completed_at = datetime.utcnow()
            db.commit()

            return ExtractionResponse(
                task_id=task_id,
                status="completed",
                cases_extracted=len(cases),
                cases_stored=stored_count,
                message=f"Successfully extracted and stored {stored_count} cases",
            )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in extract_cases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/task/{task_id}",
    response_model=ExtractionTaskResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
) -> ExtractionTaskResponse:
    """Get extraction task status and progress"""
    task = db.query(ExtractionTask).filter(
        ExtractionTask.task_id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return ExtractionTaskResponse.from_orm(task)


async def background_batch_extraction(
    task_id: str,
    db: Session,
    force_refresh: bool = False,
    batch_size: int = 500,
    timeout: int = 120,
    threads: int = 8,
) -> None:
    """Background task for batch extracting ALL ECHR cases"""
    try:
        # Update task status to running
        task = db.query(ExtractionTask).filter(
            ExtractionTask.task_id == task_id
        ).first()
        if task:
            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()

        # Run batch extraction
        stats = await batch_extract_all_cases(
            db_session=db,
            force_refresh=force_refresh,
            batch_size=batch_size,
            timeout=timeout,
            threads=threads,
        )

        # Update task with results
        if task:
            task.status = "completed"
            task.cases_extracted = stats.get("total_extracted", 0)
            task.cases_stored = stats.get("total_stored", 0)
            task.completed_at = datetime.utcnow()
            
            # Store summary in error_message field (reusing for metadata)
            completed = len(stats.get("years_completed", []))
            failed = len(stats.get("years_failed", []))
            duration = stats.get("duration_seconds", 0)
            task.error_message = (
                f"Completed: {completed} years, "
                f"Failed: {failed} years, "
                f"Duration: {duration:.1f}s"
            )
            db.commit()

        logger.info(
            f"Batch extraction task {task_id} completed: "
            f"{stats.get('total_extracted', 0)} extracted, "
            f"{stats.get('total_stored', 0)} stored"
        )

    except Exception as e:
        logger.error(f"Error in background batch extraction task {task_id}: {e}")
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()


@router.post(
    "/extract-all-cases",
    response_model=BatchExtractionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def extract_all_cases(
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> BatchExtractionResponse:
    """
    Extract ALL available ECHR cases (~70,000) by batch downloading per year
    Runs as a background task and is resumable
    
    Parameters:
    - force_refresh: If true, re-download all years regardless of database state
    
    Returns:
    - Batch extraction task response with tracking ID
    
    Progress can be checked using: GET /api/v1/task/{task_id}
    """
    try:
        task_id = str(uuid.uuid4())

        # Create task record
        extraction_task = ExtractionTask(
            task_id=task_id,
            status="pending",
            count=None,
            start_date=None,
            end_date=None,
            language="ENG",
            max_items=None,
        )
        db.add(extraction_task)
        db.commit()

        # Add batch extraction to background tasks
        background_tasks.add_task(
            background_batch_extraction,
            task_id=task_id,
            db=db,
            force_refresh=force_refresh,
            batch_size=500,
            timeout=120,
            threads=8,
        )

        return BatchExtractionResponse(
            task_id=task_id,
            status="pending",
            total_extracted=0,
            total_stored=0,
            years_completed=[],
            years_skipped=[],
            years_failed=[],
            message="Batch extraction started. Use GET /api/v1/task/{task_id} to check progress.",
            progress_percent=0,
        )

    except Exception as e:
        logger.error(f"Error starting batch extraction: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch extraction")
