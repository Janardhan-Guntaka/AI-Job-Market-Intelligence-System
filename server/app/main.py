from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from app.database import engine, get_db
from app.models import job as job_model
from app.models import user as user_model
from app.models import resume as resume_model
from app.api.jobs import router as jobs_router
from app.api.auth import router as auth_router
from app.api.resume import router as resume_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Create all DB tables (including new Resume table)
job_model.Base.metadata.create_all(bind=engine)
user_model.Base.metadata.create_all(bind=engine)
resume_model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareerOps AI — Job Intelligence API",
    description=(
        "AI-powered career intelligence platform. "
        "Upload your resume, get semantic job matches powered by LangChain RAG, "
        "and explore real-time job data from 5 major portals."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix="/api", tags=["jobs"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(resume_router, prefix="/api", tags=["resume"])


@app.on_event("startup")
async def startup_event():
    logger.info("CareerOps AI API v2.0 starting up …")
    logger.info("Database tables initialized.")


@app.get("/")
def root():
    return {
        "name": "CareerOps AI — Job Intelligence API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Multi-portal job scraping (Remotive, RemoteOK, Jobicy, WeWorkRemotely, Adzuna)",
            "Resume upload + parsing (PDF, DOCX, TXT)",
            "AI job matching with LangChain RAG + FAISS",
            "GPT-3.5-turbo personalized job explanations",
            "Real-time market analytics",
        ],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
