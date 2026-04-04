import httpx
import json
import re
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from app.models.job import Job

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


def extract_salary(salary_str: str):
    """
    Attempts to extract integer min and max salary from a free-text salary string.
    Returns (min_salary, max_salary).
    """
    if not salary_str:
        return 0.0, 0.0

    # Look for patterns like $100k, 100,000, 100k-150k, etc.
    # Simplify: find all numbers (k = 1000)
    salary_str = salary_str.lower().replace(",", "")

    # Simple regex to catch numbers followed optionally by k
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(k|m)?", salary_str)

    amounts = []
    for num, multiplier in matches:
        val = float(num)
        if multiplier == 'k' or val < 1000:
            val *= 1000
        if multiplier == 'm':
            val *= 1000000
        amounts.append(val)

    if not amounts:
        return 0.0, 0.0

    amounts.sort()
    # Assume the lowest represents min and highest represents max (if multiple)
    if len(amounts) == 1:
        return float(amounts[0]), float(amounts[0])
    return float(amounts[0]), float(amounts[-1])


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Basic BS4 to strip HTML tags for our description
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(raw_html, "html.parser").get_text(separator=" ").strip()
    except Exception:
        # Fallback if bs4 is not installed though it should be
        return re.sub(r'<[^>]+>', ' ', raw_html).strip()


def fetch_jobs_from_api(limit: int = 150) -> List[dict]:
    """Fetch real jobs from Remotive API."""
    print(f"Fetching jobs from {REMOTIVE_API_URL} (limit: {limit})")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{REMOTIVE_API_URL}?limit={limit}")
        response.raise_for_status()
        data = response.json()
        return data.get("jobs", [])


def run_daily_scraper(db: Session, max_jobs: int = 150):
    """
    Pulls data from a real job board API, maps it to our SQLAlchemy models,
    and inserts it into the database. Avoids duplicates by matching title + company.
    """
    raw_jobs = fetch_jobs_from_api(limit=max_jobs)
    print(f"Scraped {len(raw_jobs)} job postings. Parsing and inserting...")

    inserted_count = 0
    updated_count = 0

    for raw in raw_jobs:
        title = raw.get("title", "Unknown Title")
        company = raw.get("company_name", "Unknown Company")

        # Check if exists
        existing = db.query(Job).filter(Job.title == title, Job.company == company).first()

        salary_str = raw.get("salary", "")
        sal_min, sal_max = extract_salary(salary_str)

        # Determine experience level loosely
        desc = (raw.get("description", "")).lower()
        title_lower = title.lower()
        exp_level = "Mid"
        if "senior" in title_lower or "senior" in desc:
            exp_level = "Senior"
        elif "lead" in title_lower or "lead" in desc:
            exp_level = "Lead"
        elif "entry" in title_lower or "junior" in title_lower:
            exp_level = "Entry"
        elif "principal" in title_lower:
            exp_level = "Principal"
        elif "staff" in title_lower:
            exp_level = "Staff"

        tags = raw.get("tags", [])
        if not tags:
            # Fallback extracting common skills from description
            common = ["Python", "React", "JavaScript", "SQL", "AWS", "Docker", "Java", "C++", "Ruby", "Go"]
            for c in common:
                if c.lower() in desc:
                    tags.append(c)

        try:
            posted_date = datetime.strptime(raw.get("publication_date", ""), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            posted_date = datetime.utcnow()

        if existing:
            # Update
            existing.salary_min = sal_min
            existing.salary_max = sal_max
            existing.skills = json.dumps(tags)
            existing.posted_date = posted_date
            updated_count += 1
        else:
            # Insert
            new_job = Job(
                title=title,
                company=company,
                location=raw.get("candidate_required_location", "Remote"),
                remote="Remote" if "remote" in raw.get("job_type", "").lower() or True else "Hybrid",
                category=raw.get("category", "Software Engineering"),
                salary_min=sal_min,
                salary_max=sal_max,
                skills=json.dumps(tags),
                experience_level=exp_level,
                posted_date=posted_date,
                description=clean_html(raw.get("description", ""))
            )
            db.add(new_job)
            inserted_count += 1

    db.commit()
    print(f"Scraping complete! Inserted: {inserted_count}, Updated: {updated_count}")
