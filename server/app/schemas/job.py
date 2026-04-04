from pydantic import BaseModel
from datetime import datetime
from typing import List


class JobBase(BaseModel):
    title: str
    company: str
    location: str
    remote: str
    category: str
    salary_min: float
    salary_max: float
    skills: str
    experience_level: str
    description: str


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    posted_date: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    jobs: List[JobResponse]
    page: int
    pages: int


class SkillStat(BaseModel):
    skill: str
    count: int
    avg_salary: float


class SalaryStat(BaseModel):
    category: str
    avg_min: float
    avg_max: float
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int
    avg_salary: float
