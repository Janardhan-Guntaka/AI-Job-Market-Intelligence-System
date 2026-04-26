"""
Resume API Routes
=================
POST /api/resume/upload  — Upload PDF/DOCX, parse, store in DB
GET  /api/resume/me      — Get current user's resume summary
DELETE /api/resume/me    — Delete current user's resume
POST /api/resume/match   — Run AI job matching against resume
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.services.resume_parser import parse_resume
from app.services.rag_pipeline import match_jobs_to_resume
from app.api.auth import get_current_user  # we'll add this helper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])

# Max 5 MB upload
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class ResumeResponse(BaseModel):
    id: int
    filename: str
    skills: List[str]
    experience_level: str
    years_experience: str
    job_titles: List[str]
    has_resume: bool = True

    class Config:
        from_attributes = True


class MatchedJobItem(BaseModel):
    id: int
    title: str
    company: str
    location: str
    remote: str
    category: str
    salary_min: float
    salary_max: float
    skills: List[str]
    experience_level: str
    source: Optional[str] = None
    apply_url: Optional[str] = None
    match_score: float
    match_pct: int
    ai_explanation: str


class MatchResponse(BaseModel):
    total: int
    jobs: List[MatchedJobItem]
    resume_skills: List[str]
    openai_powered: bool


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload a resume file (PDF, DOCX, or TXT).
    Parses skills, experience level, and stores the result.
    """
    # Validate extension
    filename = file.filename or "resume"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Please upload PDF, DOCX, or TXT.",
        )

    # Read and size-check
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum allowed size is 5 MB.",
        )

    # Parse
    try:
        parsed = parse_resume(file_bytes, filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Resume parse error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parse error: {exc}")

    # Upsert to DB (one resume per user)
    existing = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if existing:
        existing.filename = filename
        existing.raw_text = parsed["raw_text"]
        existing.parsed_skills = json.dumps(parsed["skills"])
        existing.experience_level = parsed["experience_level"]
        existing.years_experience = parsed["years_experience"]
        existing.job_titles = json.dumps(parsed["job_titles"])
        resume_record = existing
    else:
        resume_record = Resume(
            user_id=current_user.id,
            filename=filename,
            raw_text=parsed["raw_text"],
            parsed_skills=json.dumps(parsed["skills"]),
            experience_level=parsed["experience_level"],
            years_experience=parsed["years_experience"],
            job_titles=json.dumps(parsed["job_titles"]),
        )
        db.add(resume_record)

    db.commit()
    db.refresh(resume_record)

    return ResumeResponse(
        id=resume_record.id,
        filename=resume_record.filename,
        skills=parsed["skills"],
        experience_level=parsed["experience_level"],
        years_experience=parsed["years_experience"],
        job_titles=parsed["job_titles"],
    )


# ---------------------------------------------------------------------------
# Get my resume
# ---------------------------------------------------------------------------

@router.get("/me", response_model=ResumeResponse)
def get_my_resume(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the current user's parsed resume summary."""
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")

    return ResumeResponse(
        id=resume.id,
        filename=resume.filename,
        skills=json.loads(resume.parsed_skills or "[]"),
        experience_level=resume.experience_level or "Unknown",
        years_experience=resume.years_experience or "Unknown",
        job_titles=json.loads(resume.job_titles or "[]"),
    )


# ---------------------------------------------------------------------------
# Delete my resume
# ---------------------------------------------------------------------------

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_resume(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete the current user's resume data."""
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume to delete.")
    db.delete(resume)
    db.commit()


# ---------------------------------------------------------------------------
# AI Match endpoint
# ---------------------------------------------------------------------------

@router.post("/match", response_model=MatchResponse)
def match_resume_to_jobs(
    top_k: int = 15,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run the RAG pipeline to match the user's resume against all jobs in the DB.
    Returns top-K ranked jobs with AI-generated explainers.
    """
    # Get user's resume
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Please upload your resume first to use AI matching.",
        )

    resume_skills = json.loads(resume.parsed_skills or "[]")
    resume_text = resume.raw_text or ""

    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Resume text is empty. Please re-upload.")

    # Fetch jobs from DB (limit to recent 500 for performance)
    db_jobs = db.query(Job).order_by(Job.posted_date.desc()).limit(500).all()
    if not db_jobs:
        raise HTTPException(status_code=404, detail="No jobs in database yet. Run the scraper first.")

    job_dicts = []
    for j in db_jobs:
        job_dicts.append({
            "id": j.id,
            "title": j.title or "",
            "company": j.company or "",
            "location": j.location or "",
            "remote": j.remote or "Remote",
            "category": j.category or "",
            "description": j.description or "",
            "salary_min": j.salary_min or 0.0,
            "salary_max": j.salary_max or 0.0,
            "skills": j.skills or "[]",
            "experience_level": j.experience_level or "Mid",
            "source": j.source or "unknown",
            "apply_url": j.apply_url or "",
        })

    # Run matching
    try:
        matched = match_jobs_to_resume(
            resume_text=resume_text,
            resume_skills=resume_skills,
            db_jobs=job_dicts,
            top_k=min(top_k, 20),
        )
    except Exception as exc:
        logger.exception("Job matching pipeline failed")
        raise HTTPException(status_code=500, detail=f"Matching failed: {exc}")

    # Serialise
    result_jobs = []
    for m in matched:
        skills_list = (
            json.loads(m["skills"]) if isinstance(m["skills"], str) else m.get("skills", [])
        )
        result_jobs.append(
            MatchedJobItem(
                id=m["id"],
                title=m["title"],
                company=m["company"],
                location=m["location"],
                remote=m["remote"],
                category=m["category"],
                salary_min=m["salary_min"],
                salary_max=m["salary_max"],
                skills=skills_list if isinstance(skills_list, list) else [],
                experience_level=m["experience_level"],
                source=m.get("source"),
                apply_url=m.get("apply_url"),
                match_score=m["match_score"],
                match_pct=m["match_pct"],
                ai_explanation=m["ai_explanation"],
            )
        )

    import os
    return MatchResponse(
        total=len(result_jobs),
        jobs=result_jobs,
        resume_skills=resume_skills,
        openai_powered=bool(os.getenv("OPENAI_API_KEY")),
    )
