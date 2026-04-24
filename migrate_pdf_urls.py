#!/usr/bin/env python3
"""
Migration script to add pdf_url to existing cases
"""

from database import Case, SessionLocal, engine
from config import get_settings
import logging
import sqlite3
import os
import json
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Extract database path from SQLite URL"""
    settings = get_settings()
    db_url = settings.DATABASE_URL
    # Format: sqlite:///./echr_dashboard.db
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return db_url

def migrate_pdf_urls():
    """Add pdf_url column and populate it for all existing cases"""
    db = SessionLocal()
    
    try:
        # Get the database file path
        db_path = get_db_path()
        logger.info(f"Using database: {db_path}")
        
        # First, add the column if it doesn't exist (SQLite specific)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('ALTER TABLE cases ADD COLUMN pdf_url VARCHAR(500)')
            conn.commit()
            logger.info("✓ Added pdf_url column to cases table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                logger.info("✓ pdf_url column already exists")
            else:
                raise
        finally:
            conn.close()
        
        # Now update the cases
        cases = db.query(Case).all()
        
        if not cases:
            logger.info("✓ No cases found in database")
            return
        
        logger.info(f"Updating {len(cases)} cases with pdf_url...")
        
        updated = 0
        for case in cases:
            if case.itemid and case.itemid.startswith('001-'):
                # itemid is already in correct format (001-XXXXX)
                case.pdf_url = f'https://hudoc.echr.coe.int/#{quote(json.dumps({"documentcollectionid2": ["CHAMBER"], "itemid": [case.itemid]}, separators=(",", ":")), safe="")}'
                updated += 1
                
                if updated % 100 == 0:
                    db.commit()
                    logger.info(f"  Updated {updated} cases...")
        
        db.commit()
        logger.info(f"✓ Successfully updated {updated} cases with pdf_url")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_pdf_urls()
