"""
Multi-Portal Job Scraper
========================
Aggregates job listings from multiple free, API-friendly sources:
  - Remotive       (https://remotive.com/api)
  - RemoteOK       (https://remoteok.com/api)
  - Jobicy         (https://jobicy.com/api/v2/remote-jobs)
  - We Work Remotely (HTML scrape of public feed)
  - Adzuna         (https://api.adzuna.com — free dev key required)

All scrapers deduplicate via `source_url` so running multiple times
will upsert rather than create duplicates.
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.job import Job

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared data class — every scraper produces these
# ---------------------------------------------------------------------------

@dataclass
class ScrapedJob:
    title: str
    company: str
    location: str
    remote: str          # "Remote" | "Hybrid" | "On-site"
    category: str
    description: str
    source: str          # portal slug
    source_url: str      # canonical dedup key (unique)
    apply_url: str = ""
    salary_min: float = 0.0
    salary_max: float = 0.0
    skills: List[str] = field(default_factory=list)
    experience_level: str = "Mid"
    posted_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

COMMON_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Node.js", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "Java", "Go", "Rust", "C++", "C#", ".NET", "Ruby", "PHP",
    "FastAPI", "Django", "Flask", "Spring", "Next.js", "GraphQL",
    "REST", "gRPC", "Kafka", "Spark", "Airflow", "dbt", "Tableau",
    "PyTorch", "TensorFlow", "Scikit-learn", "LangChain", "OpenAI",
    "Linux", "Git", "CI/CD", "Agile", "Scrum",
]


def extract_salary(salary_str: str) -> tuple[float, float]:
    """Parse a free-text salary string into (min, max) floats."""
    if not salary_str:
        return 0.0, 0.0
    salary_str = salary_str.lower().replace(",", "").replace("$", "")
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(k|m)?", salary_str)
    amounts: List[float] = []
    for num, multiplier in matches:
        val = float(num)
        if multiplier == "k" or (val < 1000 and val > 0):
            val *= 1000
        elif multiplier == "m":
            val *= 1_000_000
        if 10_000 < val < 2_000_000:  # sanity filter
            amounts.append(val)
    if not amounts:
        return 0.0, 0.0
    amounts.sort()
    return amounts[0], amounts[-1] if len(amounts) > 1 else amounts[0]


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known tech skills from a job description."""
    text_lower = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        # Word-boundary aware match to avoid false positives
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and return clean plain text."""
    if not raw_html:
        return ""
    try:
        return BeautifulSoup(raw_html, "html.parser").get_text(separator=" ").strip()
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw_html).strip()


def infer_experience_level(title: str, description: str) -> str:
    """Determine seniority from title and description keywords."""
    combined = (title + " " + description).lower()
    if any(k in combined for k in ["principal", "distinguished", "fellow"]):
        return "Principal"
    if any(k in combined for k in ["staff engineer", "staff swe"]):
        return "Staff"
    if any(k in combined for k in ["lead ", "tech lead", "team lead"]):
        return "Lead"
    if any(k in combined for k in ["senior", "sr.", "sr "]):
        return "Senior"
    if any(k in combined for k in ["junior", "jr.", "entry", "associate", "graduate", "intern"]):
        return "Entry"
    return "Mid"


def parse_date(date_str: str, fmt: str = "%Y-%m-%dT%H:%M:%S") -> datetime:
    """Parse a date string, falling back to now."""
    for f in [fmt, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.strptime(date_str, f)
        except (ValueError, TypeError):
            continue
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Base scraper contract
# ---------------------------------------------------------------------------

class BasePortalScraper(ABC):
    """All portal scrapers must implement `fetch()`."""

    name: str = "base"
    timeout: int = 30

    def fetch(self) -> List[ScrapedJob]:
        """Fetch jobs; returns empty list on any error."""
        try:
            return self._fetch()
        except Exception as exc:
            logger.warning("[%s] scraper failed: %s", self.name, exc)
            return []

    @abstractmethod
    def _fetch(self) -> List[ScrapedJob]:
        ...


# ---------------------------------------------------------------------------
# Remotive scraper
# ---------------------------------------------------------------------------

class RemotiveScraper(BasePortalScraper):
    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"

    def _fetch(self) -> List[ScrapedJob]:
        logger.info("[remotive] fetching jobs …")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.API_URL}?limit=200")
            resp.raise_for_status()
            raw_jobs = resp.json().get("jobs", [])

        results = []
        for raw in raw_jobs:
            title = raw.get("title", "Unknown Title")
            desc = clean_html(raw.get("description", ""))
            tags = raw.get("tags", []) or extract_skills_from_text(desc)
            sal_min, sal_max = extract_salary(raw.get("salary", ""))
            job_type = raw.get("job_type", "").lower()
            remote_type = "Remote" if "remote" in job_type or "full_time" in job_type else "Hybrid"

            results.append(ScrapedJob(
                title=title,
                company=raw.get("company_name", "Unknown"),
                location=raw.get("candidate_required_location", "Worldwide"),
                remote=remote_type,
                category=raw.get("category", "Software Engineering"),
                description=desc,
                source=self.name,
                source_url=raw.get("url", ""),
                apply_url=raw.get("url", ""),
                salary_min=sal_min,
                salary_max=sal_max,
                skills=tags,
                experience_level=infer_experience_level(title, desc),
                posted_date=parse_date(raw.get("publication_date", "")),
            ))
        logger.info("[remotive] fetched %d jobs", len(results))
        return results


# ---------------------------------------------------------------------------
# RemoteOK scraper
# ---------------------------------------------------------------------------

class RemoteOKScraper(BasePortalScraper):
    name = "remoteok"
    API_URL = "https://remoteok.com/api"

    def _fetch(self) -> List[ScrapedJob]:
        logger.info("[remoteok] fetching jobs …")
        headers = {"User-Agent": "CareerOps-AI/1.0 (open-source job intelligence)"}
        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            resp = client.get(self.API_URL)
            resp.raise_for_status()
            data = resp.json()

        # First element is a metadata object, skip it
        raw_jobs = [j for j in data if isinstance(j, dict) and "id" in j]

        results = []
        for raw in raw_jobs:
            title = raw.get("position", "Unknown Title")
            desc = clean_html(raw.get("description", ""))
            tags = raw.get("tags", []) or extract_skills_from_text(desc)
            sal_min, sal_max = extract_salary(raw.get("salary", ""))
            slug = raw.get("slug", str(raw.get("id", "")))
            url = f"https://remoteok.com/remote-jobs/{slug}"

            results.append(ScrapedJob(
                title=title,
                company=raw.get("company", "Unknown"),
                location="Worldwide",
                remote="Remote",
                category=", ".join(tags[:2]) if tags else "Software Engineering",
                description=desc,
                source=self.name,
                source_url=url,
                apply_url=raw.get("apply_url", url),
                salary_min=sal_min,
                salary_max=sal_max,
                skills=tags,
                experience_level=infer_experience_level(title, desc),
                posted_date=parse_date(str(raw.get("date", ""))),
            ))
        logger.info("[remoteok] fetched %d jobs", len(results))
        return results


# ---------------------------------------------------------------------------
# Jobicy scraper
# ---------------------------------------------------------------------------

class JobicyScraper(BasePortalScraper):
    name = "jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs?count=50&geo=worldwide"

    def _fetch(self) -> List[ScrapedJob]:
        logger.info("[jobicy] fetching jobs …")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(self.API_URL)
            resp.raise_for_status()
            raw_jobs = resp.json().get("jobs", [])

        results = []
        for raw in raw_jobs:
            title = raw.get("jobTitle", "Unknown Title")
            desc = clean_html(raw.get("jobDescription", ""))
            skills_raw = raw.get("jobIndustry", [])
            if isinstance(skills_raw, str):
                skills_raw = [skills_raw]
            skills = skills_raw + extract_skills_from_text(desc)
            skills = list(dict.fromkeys(skills))[:15]  # dedup + cap

            sal_min, sal_max = extract_salary(raw.get("annualSalaryMin", "") or raw.get("annualSalaryMax", ""))
            url = raw.get("url", f"https://jobicy.com/?feed=job_feed&job_id={raw.get('id', '')}")

            results.append(ScrapedJob(
                title=title,
                company=raw.get("companyName", "Unknown"),
                location=raw.get("jobGeo", "Worldwide"),
                remote="Remote",
                category=raw.get("jobIndustry", ["Software Engineering"])[0] if isinstance(raw.get("jobIndustry"), list) else raw.get("jobIndustry", "Software Engineering"),
                description=desc,
                source=self.name,
                source_url=url,
                apply_url=url,
                salary_min=sal_min,
                salary_max=sal_max,
                skills=skills,
                experience_level=infer_experience_level(title, desc),
                posted_date=parse_date(raw.get("pubDate", "")),
            ))
        logger.info("[jobicy] fetched %d jobs", len(results))
        return results


# ---------------------------------------------------------------------------
# We Work Remotely scraper (RSS feed — public, no key needed)
# ---------------------------------------------------------------------------

class WeWorkRemotelyScraper(BasePortalScraper):
    name = "weworkremotely"
    RSS_URL = "https://weworkremotely.com/remote-jobs.rss"

    def _fetch(self) -> List[ScrapedJob]:
        logger.info("[weworkremotely] fetching RSS …")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(self.RSS_URL)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")

        results = []
        for item in items:
            title_full = item.find("title").get_text(strip=True) if item.find("title") else ""
            # Title format: "Company: Job Title"
            if ":" in title_full:
                company, title = title_full.split(":", 1)
                company = company.strip()
                title = title.strip()
            else:
                title = title_full
                company = "Unknown"

            link = item.find("link").get_text(strip=True) if item.find("link") else ""
            desc = clean_html(item.find("description").get_text() if item.find("description") else "")
            pub_date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
            region = item.find("region").get_text(strip=True) if item.find("region") else "Worldwide"
            category_tag = item.find("category")
            category = category_tag.get_text(strip=True) if category_tag else "Software Engineering"

            skills = extract_skills_from_text(desc)

            results.append(ScrapedJob(
                title=title,
                company=company,
                location=region or "Worldwide",
                remote="Remote",
                category=category,
                description=desc,
                source=self.name,
                source_url=link,
                apply_url=link,
                skills=skills,
                experience_level=infer_experience_level(title, desc),
                posted_date=parse_date(pub_date, "%a, %d %b %Y %H:%M:%S %z") if pub_date else datetime.utcnow(),
            ))
        logger.info("[weworkremotely] fetched %d jobs", len(results))
        return results


# ---------------------------------------------------------------------------
# Adzuna scraper (free dev API — needs APP_ID + APP_KEY in env)
# ---------------------------------------------------------------------------

class AdzunaScraper(BasePortalScraper):
    name = "adzuna"
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID", "")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "")

    def _fetch(self) -> List[ScrapedJob]:
        if not self.app_id or not self.app_key:
            logger.info("[adzuna] skipping — ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
            return []

        logger.info("[adzuna] fetching jobs …")
        results = []
        # Fetch from US, UK, Canada
        for country in ["us", "gb", "ca"]:
            url = f"{self.BASE_URL}/{country}/search/1"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": 50,
                "what": "software engineer OR data engineer OR product manager",
                "content-type": "application/json",
            }
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    raw_jobs = resp.json().get("results", [])
            except Exception as exc:
                logger.warning("[adzuna] %s request failed: %s", country, exc)
                continue

            for raw in raw_jobs:
                title = raw.get("title", "Unknown Title")
                desc = clean_html(raw.get("description", ""))
                redirect_url = raw.get("redirect_url", "")
                sal_min = float(raw.get("salary_min", 0) or 0)
                sal_max = float(raw.get("salary_max", 0) or 0)
                location = raw.get("location", {}).get("display_name", "Unknown")
                company = raw.get("company", {}).get("display_name", "Unknown")

                results.append(ScrapedJob(
                    title=title,
                    company=company,
                    location=location,
                    remote="Remote" if "remote" in (title + desc).lower() else "On-site",
                    category=raw.get("category", {}).get("label", "Software Engineering"),
                    description=desc,
                    source=self.name,
                    source_url=redirect_url,
                    apply_url=redirect_url,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    skills=extract_skills_from_text(desc),
                    experience_level=infer_experience_level(title, desc),
                    posted_date=parse_date(raw.get("created", "")),
                ))
        logger.info("[adzuna] fetched %d jobs total", len(results))
        return results


# ---------------------------------------------------------------------------
# Database upsert — source_url is the dedup key
# ---------------------------------------------------------------------------

def upsert_job(db: Session, job: ScrapedJob) -> tuple[str, bool]:
    """
    Insert a new job or update an existing one by source_url.
    Returns ("inserted" | "updated", success).
    """
    if not job.source_url:
        # Skip jobs with no canonical URL — can't dedup safely
        return ("skipped", False)

    existing = db.query(Job).filter(Job.source_url == job.source_url).first()

    if existing:
        existing.title = job.title
        existing.company = job.company
        existing.location = job.location
        existing.remote = job.remote
        existing.category = job.category
        existing.description = job.description
        existing.salary_min = job.salary_min
        existing.salary_max = job.salary_max
        existing.skills = json.dumps(job.skills)
        existing.experience_level = job.experience_level
        existing.apply_url = job.apply_url
        existing.source = job.source
        if job.posted_date:
            existing.posted_date = job.posted_date
        return ("updated", True)
    else:
        new_job = Job(
            title=job.title,
            company=job.company,
            location=job.location,
            remote=job.remote,
            category=job.category,
            description=job.description,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            skills=json.dumps(job.skills),
            experience_level=job.experience_level,
            posted_date=job.posted_date or datetime.utcnow(),
            source=job.source,
            source_url=job.source_url,
            apply_url=job.apply_url,
        )
        db.add(new_job)
        return ("inserted", True)


# ---------------------------------------------------------------------------
# Main orchestrator — runs all scrapers, returns summary
# ---------------------------------------------------------------------------

ALL_SCRAPERS: List[BasePortalScraper] = [
    RemotiveScraper(),
    RemoteOKScraper(),
    JobicyScraper(),
    WeWorkRemotelyScraper(),
    AdzunaScraper(),
]


def run_daily_scraper(db: Session, max_jobs: int = 200) -> dict:
    """
    Orchestrate all portal scrapers, upsert to DB, return summary stats.
    """
    summary = {
        "total_fetched": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "by_portal": {},
    }

    for scraper in ALL_SCRAPERS:
        portal_jobs = scraper.fetch()
        portal_inserted = portal_updated = portal_error = 0

        for job in portal_jobs[:max_jobs]:
            try:
                action, success = upsert_job(db, job)
                if action == "inserted":
                    portal_inserted += 1
                elif action == "updated":
                    portal_updated += 1
                else:
                    portal_error += 1
            except IntegrityError:
                db.rollback()
                portal_error += 1
            except Exception as exc:
                db.rollback()
                logger.error("[%s] upsert error: %s", scraper.name, exc)
                portal_error += 1

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("[%s] commit error: %s", scraper.name, exc)

        summary["total_fetched"] += len(portal_jobs)
        summary["inserted"] += portal_inserted
        summary["updated"] += portal_updated
        summary["errors"] += portal_error
        summary["by_portal"][scraper.name] = {
            "fetched": len(portal_jobs),
            "inserted": portal_inserted,
            "updated": portal_updated,
        }
        logger.info(
            "[%s] done — inserted: %d, updated: %d, errors: %d",
            scraper.name, portal_inserted, portal_updated, portal_error
        )

    logger.info("Scraping complete: %s", summary)
    return summary
