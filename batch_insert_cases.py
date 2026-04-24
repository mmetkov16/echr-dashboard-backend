#!/usr/bin/env python3
"""
Batch insert ECHR cases into database using date range filtering
Much more efficient than fetching all data at once
"""

from echr_extractor import get_echr
from database import Case, SessionLocal
from datetime import datetime
import json
from urllib.parse import quote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_date(date_value):
    """Parse date string to datetime object"""
    if not date_value or date_value == 'nan':
        return None
    
    date_str = str(date_value).strip()
    
    # Try multiple date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.debug(f"Could not parse date: {date_value}")
    return None

def insert_cases_for_year(year: int):
    """Fetch and insert cases for a specific year"""
    db = SessionLocal()
    
    try:
        logger.info(f"Fetching cases for year {year}...")
        
        # Fetch with date range filtering
        df = get_echr(
            start_date=f"{year}-01-01",
            end_date=f"{year}-12-31",
            batch_size=500,
            timeout=120
        )
        
        if df.empty:
            logger.info(f"No cases found for year {year}")
            return 0
        
        logger.info(f"Processing {len(df)} records for year {year}...")
        
        # Convert DataFrame to cases and insert
        inserted = 0
        skipped = 0
        for _, row in df.iterrows():
            try:
                # Use appno as unique identifier (itemid not reliable)
                appno = row.get("appno", "")
                if not appno:
                    skipped += 1
                    continue
                
                # Check if already exists by appno
                existing = db.query(Case).filter(Case.appno == appno).first()
                if existing:
                    skipped += 1
                    continue
                
                # Create case object with safe defaults
                itemid = appno
                case_data = {
                    "itemid": itemid,  # Use appno as itemid
                    "appno": appno,
                    "docname": str(row.get("docname", ""))[:500],
                    "country": str(row.get("respondent", ""))[:100],
                    "article": str(row.get("article", ""))[:500],
                    "violation": bool(row.get("violation")),
                    "violation_count": 1 if row.get("violation") else 0,
                    "judgementdate": parse_date(row.get("judgementdate")),  # Use judgementdate, not referencedate
                    "status": str(row.get("conclusion", ""))[:500],
                    "conclusion": str(row.get("conclusion", ""))[:500],
                    "title": str(row.get("docname", ""))[:500],
                    "description": "",
                    "respondent": str(row.get("respondent", ""))[:100],
                    "applicant": str(row.get("applicantname", ""))[:500],
                    "language": str(row.get("languageisocode", "ENG"))[:10],
                    "is_important": bool(row.get("importance")),
                    "citation_count": 0,
                    "pdf_url": f'https://hudoc.echr.coe.int/#{quote(json.dumps({"itemid": [itemid]}, separators=(",", ":")), safe="")}',
                }
                
                case = Case(**case_data)
                db.add(case)
                inserted += 1
                
                # Commit every 100 cases
                if inserted % 100 == 0:
                    db.commit()
                    logger.info(f"  Inserted {inserted} cases, skipped {skipped}...")
                    
            except Exception as e:
                db.rollback()
                logger.debug(f"Error inserting case: {e}")
                skipped += 1
                continue
        
        db.commit()
        logger.info(f"✓ Year {year}: Inserted {inserted} cases (skipped {skipped})")
        return inserted
        
    except Exception as e:
        logger.error(f"Error fetching cases for year {year}: {e}")
        return 0
    finally:
        db.close()


def main():
    """Fetch and insert cases for all years"""
    logger.info("Starting batch case insertion...")
    
    total_inserted = 0
    
    # Years to fetch (start from 1990s for faster initial test)
    years = list(range(1990, 2027))
    
    for year in years:
        try:
            inserted = insert_cases_for_year(year)
            total_inserted += inserted
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error for year {year}: {e}")
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Batch insertion complete!")
    logger.info(f"Total cases inserted: {total_inserted}")
    logger.info(f"{'='*60}")
    
    # Verify
    db = SessionLocal()
    total_in_db = db.query(Case).count()
    logger.info(f"Total cases in database: {total_in_db}")
    db.close()


if __name__ == "__main__":
    main()
