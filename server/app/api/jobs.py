from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.job import Job
from app.schemas.job import (
    JobResponse, JobListResponse, SkillStat, SalaryStat, TrendPoint
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "message": "AI Job Market Intelligence API is running"}


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    remote: Optional[str] = None,
    experience: Optional[str] = None,
    min_salary: Optional[float] = None,
):
    query = db.query(Job)

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") | 
            Job.company.ilike(f"%{search}%") |
            Job.skills.ilike(f"%{search}%") |
            Job.category.ilike(f"%{search}%")
        )
    if category:
        query = query.filter(Job.category == category)
    if remote:
        query = query.filter(Job.remote == remote)
    if experience:
        query = query.filter(Job.experience_level == experience)
    if min_salary:
        query = query.filter(Job.salary_min >= min_salary)

    query = query.order_by(Job.posted_date.desc())
    total = query.count()
    jobs = query.offset((page - 1) * limit).limit(limit).all()

    return JobListResponse(
        total=total,
        jobs=jobs,
        page=page,
        pages=(total + limit - 1) // limit,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/stats/skills")
def skill_stats(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    skill_map: dict = {}

    for job in jobs:
        skills = json.loads(job.skills or "[]")
        avg_sal = (job.salary_min + job.salary_max) / 2
        for skill in skills:
            if skill not in skill_map:
                skill_map[skill] = {"count": 0, "total_salary": 0.0}
            skill_map[skill]["count"] += 1
            skill_map[skill]["total_salary"] += avg_sal

    result = [
        SkillStat(
            skill=skill,
            count=data["count"],
            avg_salary=round(data["total_salary"] / data["count"], 2),
        )
        for skill, data in skill_map.items()
    ]
    return sorted(result, key=lambda x: x.count, reverse=True)[:20]


@router.get("/stats/salary")
def salary_stats(db: Session = Depends(get_db)):
    results = (
        db.query(
            Job.category,
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max"),
            func.count(Job.id).label("count"),
        )
        .group_by(Job.category)
        .all()
    )
    return [
        SalaryStat(
            category=r.category,
            avg_min=round(r.avg_min, 2),
            avg_max=round(r.avg_max, 2),
            count=r.count,
        )
        for r in results
    ]


@router.get("/stats/trends")
def trend_stats(db: Session = Depends(get_db)):
    base = datetime.utcnow()
    results = []
    for i in range(12, 0, -1):
        start = base - timedelta(days=i * 7)
        end = base - timedelta(days=(i - 1) * 7)
        week_jobs = db.query(Job).filter(
            Job.posted_date >= start, Job.posted_date < end
        ).all()
        count = len(week_jobs)
        avg_sal = (
            round(sum((j.salary_min + j.salary_max) / 2 for j in week_jobs) / count, 2)
            if count
            else 0
        )
        results.append(
            TrendPoint(date=start.strftime("%b %d"), count=count, avg_salary=avg_sal)
        )
    return results


@router.get("/stats/summary")
def summary_stats(db: Session = Depends(get_db)):
    total = db.query(Job).count()
    avg_min = db.query(func.avg(Job.salary_min)).scalar() or 0
    avg_max = db.query(func.avg(Job.salary_max)).scalar() or 0
    remote_count = db.query(Job).filter(Job.remote == "Remote").count()
    categories = db.query(Job.category, func.count(Job.id)).group_by(Job.category).all()
    top_companies = (
        db.query(Job.company, func.count(Job.id).label("cnt"))
        .group_by(Job.company)
        .order_by(func.count(Job.id).desc())
        .limit(5)
        .all()
    )
    return {
        "total_jobs": total,
        "avg_salary_min": round(float(avg_min), 2),
        "avg_salary_max": round(float(avg_max), 2),
        "remote_jobs": remote_count,
        "remote_pct": round(remote_count / total * 100, 1) if total else 0,
        "categories": {c: n for c, n in categories},
        "top_companies": {c: n for c, n in top_companies},
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Job.category).distinct().all()
    return [c[0] for c in cats]
