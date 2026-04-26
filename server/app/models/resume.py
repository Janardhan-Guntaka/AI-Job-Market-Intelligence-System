from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class Resume(Base):
    """Stores a user's uploaded resume and its parsed metadata."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(500))
    raw_text = Column(Text)                 # full extracted text
    parsed_skills = Column(Text)            # JSON list of detected skills
    experience_level = Column(String(50))   # Entry / Mid / Senior / Lead
    years_experience = Column(String(20))   # e.g. "3-5 years"
    job_titles = Column(Text)               # JSON list of likely job titles
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
