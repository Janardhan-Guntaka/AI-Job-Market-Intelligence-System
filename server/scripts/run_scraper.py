"""
run_scraper.py
==============
Standalone script to run the multi-portal job scraper.
Used by GitHub Actions (daily_scraper.yml) and for local seeding.

Usage:
    cd server
    python scripts/run_scraper.py

Environment variables (from server/.env):
    OPENAI_API_KEY   — optional, enables AI explanations
    ADZUNA_APP_ID    — optional, enables Adzuna portal
    ADZUNA_APP_KEY   — optional, enables Adzuna portal
"""

import sys
import os
import logging

# Add the /server directory to Python path so we can import 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("run_scraper")

from app.database import SessionLocal, engine
from app.models import job as job_model
from app.models import resume as resume_model
from app.models import user as user_model
from app.services.scraper import run_daily_scraper, ALL_SCRAPERS


def main():
    logger.info("=== CareerOps AI — Multi-Portal Job Scraper ===")
    logger.info("Portals enabled: %s", [s.name for s in ALL_SCRAPERS])

    # Ensure tables exist
    job_model.Base.metadata.create_all(bind=engine)
    user_model.Base.metadata.create_all(bind=engine)
    resume_model.Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")

    db = SessionLocal()
    try:
        summary = run_daily_scraper(db, max_jobs=200)
        logger.info("=== Scraping Summary ===")
        logger.info("Total fetched : %d", summary["total_fetched"])
        logger.info("Inserted      : %d", summary["inserted"])
        logger.info("Updated       : %d", summary["updated"])
        logger.info("Skipped/Err   : %d", summary["skipped"] + summary["errors"])
        logger.info("By portal     : %s", summary["by_portal"])
    except Exception as exc:
        logger.exception("Fatal error during scraping: %s", exc)
        sys.exit(1)
    finally:
        db.close()

    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
