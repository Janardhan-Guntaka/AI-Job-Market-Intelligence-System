from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import job as job_model
from app.models import user as user_model
from app.api.jobs import router as jobs_router
from app.api.auth import router as auth_router

# Create tables
job_model.Base.metadata.create_all(bind=engine)
user_model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Job Market Intelligence API",
    description="Real-time job market intelligence with salary trends, skill demand analysis, and hiring velocity metrics.",
    version="1.0.0",
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


@app.on_event("startup")
async def startup_event():
    # Database tables are created above.
    # The data pipe is now exclusively populated asynchronously by our daily scraper GitHub Action.
    pass


@app.get("/")
def root():
    return {
        "name": "AI Job Market Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
    }
