from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    company = Column(String(200), index=True)
    location = Column(String(200))
    remote = Column(String(50))
    category = Column(String(100), index=True)
    salary_min = Column(Float)
    salary_max = Column(Float)
    skills = Column(Text)  # JSON string
    experience_level = Column(String(50))
    posted_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    # Multi-portal deduplication fields
    source = Column(String(100), default="remotive")       # portal name
    source_url = Column(String(1000), unique=True, index=True, nullable=True)  # canonical dedup key
    apply_url = Column(String(1000), nullable=True)        # application link
