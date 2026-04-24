"""
ECHR extraction service - integrates with echr-extractor library
"""
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from echr_extractor import get_echr, get_echr_extra

logger = logging.getLogger(__name__)


async def extract_echr_cases(
    count: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    language: str = "ENG",
    max_items: Optional[int] = None,
    fetch_full_text: bool = False,
) -> List[Dict[str, Any]]:
    """
    Extract ECHR cases using echr-extractor library
    
    Args:
        count: Number of recent cases to fetch
        start_date: Filter from date
        end_date: Filter to date
        language: Language code (default: ENG)
        max_items: Maximum items to process
        fetch_full_text: Whether to fetch full case text
        
    Returns:
        List of case dictionaries with extracted metadata
    """
    try:
        logger.info(
            f"Starting ECHR extraction: count={count}, "
            f"start_date={start_date}, end_date={end_date}, "
            f"language={language}, fetch_full_text={fetch_full_text}"
        )

        cases = []
        
        # Use get_echr_extra if full text is needed, otherwise get_echr
        if fetch_full_text:
            logger.info("Fetching cases with full text")
            data = get_echr_extra(
                num_cases=count or 100,
                relevant_docs="ALL",  # Get all documents
            )
        else:
            logger.info("Fetching cases with metadata only")
            data = get_echr(
                num_cases=count or 100,
            )

        # Process extracted data
        for item in data:
            try:
                case = process_case_item(item, language, fetch_full_text)
                
                # Apply date filters if provided
                if case.get("judgementdate"):
                    case_date = case["judgementdate"]
                    if isinstance(case_date, str):
                        case_date = datetime.fromisoformat(case_date.replace("Z", "+00:00"))
                    
                    if start_date and case_date < start_date:
                        continue
                    if end_date and case_date > end_date:
                        continue

                cases.append(case)

                # Respect max_items limit
                if max_items and len(cases) >= max_items:
                    break

            except Exception as e:
                logger.warning(f"Error processing case item: {e}")
                continue

        logger.info(f"Successfully extracted {len(cases)} cases")
        return cases

    except ImportError as e:
        logger.error(f"echr-extractor not installed or import error: {e}")
        raise Exception("ECHR extraction library not available")
    except Exception as e:
        logger.error(f"Error extracting ECHR cases: {e}")
        raise


def process_case_item(
    item: Dict[str, Any],
    language: str = "ENG",
    include_full_text: bool = False,
) -> Dict[str, Any]:
    """
    Process a single case item from echr-extractor
    
    Args:
        item: Raw case item from echr-extractor
        language: Language code
        include_full_text: Whether to include full text
        
    Returns:
        Processed case dictionary matching Case model
    """
    try:
        # Skip if item is not a dictionary
        if not isinstance(item, dict):
            return {}
        
        # Extract common fields (adjust based on actual echr-extractor output structure)
        itemid = item.get("itemid") or item.get("appno") or item.get("id") or item.get("caseNumber") or ""
        case = {
            "itemid": itemid,
            "appno": item.get("appno") or item.get("caseNumber") or item.get("id") or "",
            "docname": item.get("docname") or item.get("name") or item.get("title") or "",
            "country": extract_country(item),
            "article": extract_articles(item),
            "violation": item.get("violation", False),
            "violation_count": count_violations(item),
            # Use referencedate first, then fall back to judgementdate
            "judgementdate": parse_date(
                item.get("referencedate")  # Primary: actual date field in the data
                or item.get("judgementdate")
                or item.get("date") 
                or item.get("judgment_date")
                or item.get("decisionsdate")
            ),
            "registration_date": parse_date(item.get("registration_date") or item.get("registrationdate")),
            "decision_date": parse_date(item.get("decision_date") or item.get("decisionsdate")),
            "status": item.get("status") or item.get("result") or "Unknown",
            "conclusion": item.get("conclusion") or item.get("result") or item.get("outcome") or "",
            "title": item.get("title") or item.get("case_name") or item.get("name") or "",
            "description": item.get("description") or item.get("summary") or item.get("text") or "",
            "respondent": item.get("respondent") or item.get("defendant") or item.get("country") or "",
            "applicant": item.get("applicant") or item.get("plaintiff") or "",
            "language": language,
            "is_important": item.get("importance") or item.get("is_important") or False,
            "citation_count": item.get("citation_count") or 0,
            # Construct URL to ECHR HUDOC case page with properly URL-encoded JSON (compact format, includes documentcollectionid2)
            "pdf_url": f'https://hudoc.echr.coe.int/#{quote(json.dumps({"documentcollectionid2": ["CHAMBER"], "itemid": [itemid]}, separators=(",", ":")), safe="")}' if itemid else None,
        }

        # Include full text if available and requested
        if include_full_text:
            case["full_text"] = item.get("full_text") or item.get("text")

        # Only return if itemid is present
        if not case.get("itemid"):
            return {}

        # Remove None values to keep database clean
        case = {k: v for k, v in case.items() if v is not None}

        return case

    except Exception as e:
        logger.debug(f"Error processing case item: {e}")
        return {}


def extract_country(item: Dict[str, Any]) -> Optional[str]:
    """Extract country from case item"""
    if not isinstance(item, dict):
        return None
    
    # Try multiple possible field names
    country = (
        item.get("country")
        or item.get("respondent_country")
        or item.get("state")
    )
    
    if isinstance(country, list):
        return country[0] if country else None
    
    return country


def extract_articles(item: Dict[str, Any]) -> Optional[str]:
    """Extract violated articles from case item"""
    if not isinstance(item, dict):
        return None
    
    articles = item.get("articles") or item.get("article")
    
    if isinstance(articles, list):
        return ", ".join(str(a) for a in articles)
    
    return articles


def count_violations(item: Dict[str, Any]) -> int:
    """Count number of violations in case item"""
    if not isinstance(item, dict):
        return 0
    
    articles = extract_articles(item)
    
    if not articles:
        return 0
    
    if isinstance(articles, str):
        return len([a.strip() for a in articles.split(",") if a.strip()])
    
    if isinstance(articles, list):
        return len(articles)
    
    return 0


def parse_date(date_value: Any) -> Optional[datetime]:
    """Parse date from various formats"""
    if not date_value:
        return None
    
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, str):
        # Strip whitespace
        date_str = str(date_value).strip()
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
        
        # Try formats with optional timestamps
        formats_to_try = [
            "%Y-%m-%d %H:%M:%S",  # ISO with time
            "%Y-%m-%d",           # ISO format
            "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY with time
            "%d/%m/%Y",           # DD/MM/YYYY
            "%Y/%m/%d",           # YYYY/MM/DD
            "%d-%m-%Y",           # DD-MM-YYYY
            "%d.%m.%Y",           # DD.MM.YYYY
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    
    logger.debug(f"Could not parse date: {date_value}")
    return None


def get_years_in_database(db_session: Any) -> set:
    """
    Check which years are already present in the database
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        Set of years that have cases in the database
    """
    from database import Case
    
    try:
        # Query distinct years from database
        existing_years = set()
        results = db_session.query(Case.judgementdate).distinct().all()
        
        for result in results:
            if result[0]:
                date = result[0]
                if isinstance(date, str):
                    date = parse_date(date)
                if isinstance(date, datetime):
                    existing_years.add(date.year)
        
        logger.info(f"Found cases for years: {sorted(existing_years)}")
        return existing_years
    except Exception as e:
        logger.warning(f"Could not query existing years from database: {e}")
        return set()


def extract_cases_for_year(
    year: int,
    batch_size: int = 500,
    timeout: int = 120,
    threads: int = 8,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Extract all ECHR cases for a specific year
    
    Args:
        year: Year to extract cases for
        batch_size: Number of cases per batch (max 500)
        timeout: Request timeout in seconds
        threads: Number of parallel threads
        max_retries: Maximum retry attempts
        
    Returns:
        List of extracted cases
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Extracting cases for year {year}")
            
            # Use get_echr to fetch all recent cases (returns pandas DataFrame)
            data = get_echr()
            
            # Convert DataFrame to list of dictionaries
            if hasattr(data, 'to_dict'):
                # It's a pandas DataFrame
                items = data.to_dict('records')
                logger.info(f"Retrieved {len(items)} items from DataFrame")
                
                if len(items) > 0:
                    logger.info(f"First item keys: {list(items[0].keys())[:15]}")
            else:
                # It's already a list
                items = list(data) if not isinstance(data, list) else data
                logger.info(f"Retrieved {len(items)} items")
            
            if len(items) == 0:
                logger.warning(f"No items retrieved for year {year}")
                return []
            
            # Filter by year
            year_cases = []
            processed_count = 0
            skipped_empty_count = 0
            skipped_no_date_count = 0
            skipped_wrong_year_count = 0
            
            for item in items:
                processed_count += 1
                
                try:
                    case = process_case_item(item, language="ENG", include_full_text=False)
                    
                    # Skip empty results
                    if not case:
                        skipped_empty_count += 1
                        continue
                    
                    # Check if case is from the target year
                    case_date = case.get("judgementdate")
                    if not case_date:
                        skipped_no_date_count += 1
                        continue
                    
                    if isinstance(case_date, str):
                        case_date = parse_date(case_date)
                    
                    if isinstance(case_date, datetime):
                        if case_date.year == year:
                            year_cases.append(case)
                        else:
                            skipped_wrong_year_count += 1
                    else:
                        skipped_no_date_count += 1
                        
                except Exception as e:
                    logger.debug(f"Error processing case for year {year}: {e}")
                    continue
            
            logger.info(
                f"Year {year} stats - Processed: {processed_count}, "
                f"Empty: {skipped_empty_count}, No date: {skipped_no_date_count}, "
                f"Wrong year: {skipped_wrong_year_count}, Extracted: {len(year_cases)}"
            )
            return year_cases
            
        except Exception as e:
            retry_count += 1
            wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60s
            logger.warning(
                f"Error extracting cases for year {year} "
                f"(attempt {retry_count}/{max_retries}): {e}"
            )
            if retry_count < max_retries:
                time.sleep(wait_time)
    
    logger.error(f"Failed to extract cases for year {year} after {max_retries} retries")
    return []


async def batch_extract_all_cases(
    db_session: Any,
    force_refresh: bool = False,
    batch_size: int = 500,
    timeout: int = 120,
    threads: int = 8,
    start_year: int = 1975,
    end_year: int = 2026,
) -> Dict[str, Any]:
    """
    Extract ALL ECHR cases (~70,000) by batch downloading once, then filtering by year
    OPTIMIZED: Fetches all data once, then filters in memory for efficiency
    Resumable - checks database for existing years and skips them
    
    Args:
        db_session: SQLAlchemy database session
        force_refresh: If True, re-download all years regardless of DB state
        batch_size: Cases per batch (max 500)
        timeout: Request timeout in seconds
        threads: Number of parallel threads
        start_year: Start year for extraction (default 1975)
        end_year: End year for extraction (default 2026)
        
    Returns:
        Dictionary with extraction statistics
    """
    from database import Case
    
    try:
        stats = {
            "total_extracted": 0,
            "total_stored": 0,
            "years_completed": [],
            "years_skipped": [],
            "years_failed": [],
            "start_time": datetime.utcnow(),
        }
        
        # Get years already in database
        existing_years = set() if force_refresh else get_years_in_database(db_session)
        
        years_to_process = [
            year for year in range(start_year, end_year + 1)
            if year not in existing_years
        ]
        
        if not years_to_process:
            if force_refresh:
                logger.info("Force refresh enabled, processing all years")
                years_to_process = list(range(start_year, end_year + 1))
            else:
                logger.info("All years already processed")
                stats["end_time"] = datetime.utcnow()
                return stats
        
        total_years = len(years_to_process)
        logger.info(
            f"Starting batch extraction for {total_years} years: "
            f"{min(years_to_process)}-{max(years_to_process)}"
        )
        
        # OPTIMIZATION: Fetch ALL data once instead of per-year
        logger.info("Fetching all ECHR cases from database (this may take a few minutes)...")
        try:
            data = get_echr()
            
            # Convert DataFrame to list of dictionaries
            if hasattr(data, 'to_dict'):
                all_items = data.to_dict('records')
                logger.info(f"Retrieved {len(all_items)} total items")
            else:
                all_items = list(data) if not isinstance(data, list) else data
                logger.info(f"Retrieved {len(all_items)} total items")
        except Exception as e:
            logger.error(f"Failed to fetch cases: {e}")
            stats["years_failed"] = years_to_process
            stats["end_time"] = datetime.utcnow()
            return stats
        
        # Now filter the data for each year
        for idx, year in enumerate(years_to_process, 1):
            try:
                progress_pct = int((idx - 1) / total_years * 100)
                logger.info(
                    f"Processing year {year} ({idx}/{total_years}) "
                    f"[{progress_pct}% complete]"
                )
                
                # Filter cases for this year from all_items
                year_cases = []
                for item in all_items:
                    try:
                        case = process_case_item(item, language="ENG", include_full_text=False)
                        
                        if not case:
                            continue
                        
                        # Get judgement date
                        case_date = case.get("judgementdate")
                        if not case_date:
                            # Skip if no valid date
                            continue
                        
                        # Ensure it's a datetime object
                        if isinstance(case_date, str):
                            case_date = parse_date(case_date)
                        
                        # Only add if year matches
                        if isinstance(case_date, datetime):
                            if case_date.year == year:
                                year_cases.append(case)
                    except Exception as e:
                        logger.debug(f"Error filtering case for year {year}: {e}")
                        continue
                
                if not year_cases:
                    logger.info(f"No cases found for year {year}")
                    stats["years_skipped"].append(year)
                    continue
                
                # Store cases in database
                stored_count = 0
                for case_data in year_cases:
                    try:
                        # Check if case already exists by itemid
                        itemid = case_data.get("itemid")
                        existing = db_session.query(Case).filter(
                            Case.itemid == itemid
                        ).first()
                        
                        if not existing:
                            case = Case(**case_data)
                            db_session.add(case)
                            stored_count += 1
                        else:
                            # Update existing case
                            for key, value in case_data.items():
                                setattr(existing, key, value)
                            existing.updated_at = datetime.utcnow()
                            stored_count += 1
                    except Exception as e:
                        logger.debug(f"Error storing case {case_data.get('itemid')}: {e}")
                
                db_session.commit()
                
                stats["total_extracted"] += len(year_cases)
                stats["total_stored"] += stored_count
                stats["years_completed"].append(year)
                
                logger.info(
                    f"Year {year} complete: extracted {len(year_cases)}, stored {stored_count}"
                )
                
            except Exception as e:
                logger.error(f"Error processing year {year}: {e}")
                stats["years_failed"].append(year)
                db_session.rollback()
        
        stats["end_time"] = datetime.utcnow()
        elapsed = stats["end_time"] - stats["start_time"]
        logger.info(f"Batch extraction completed in {elapsed}")
        logger.info(f"Statistics: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in batch extraction: {e}")
        stats["error"] = str(e)
        stats["end_time"] = datetime.utcnow()
        return stats

