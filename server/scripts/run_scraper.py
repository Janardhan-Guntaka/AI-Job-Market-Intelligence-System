import sys
import os

# Add the /server directory to Python path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import job as job_model
from app.services.scraper import run_daily_scraper

def main():
    print("Initialize Database Connection...")
    # Ensure tables exist
    job_model.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # We will pull 200 jobs by default during the daily cron job run
        run_daily_scraper(db, max_jobs=200)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
