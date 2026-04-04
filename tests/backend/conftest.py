import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use pure in-memory SQLite — no file, no Windows file-lock issues
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    # Use StaticPool so all connections share the same in-memory DB
)

# StaticPool keeps one connection alive so in-memory data persists
from sqlalchemy.pool import StaticPool  # noqa: E402
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    from app.models.job import Job
    import json
    from datetime import datetime

    db = TestingSessionLocal()
    
    # Insert 5 fake jobs for tests
    categories = ["Software Development", "Data Science"]
    jobs = []
    for i in range(1, 6):
        job = Job(
            title=f"Test Engineer {i}",
            company=f"Test Corp {i}",
            location="Remote",
            remote="Remote",
            category=categories[i % 2],
            salary_min=100000.0 + (i * 5000),
            salary_max=120000.0 + (i * 5000),
            skills=json.dumps(["Python", "React"]),
            experience_level="Mid",
            posted_date=datetime.utcnow(),
            description=f"This is a test job description {i}"
        )
        db.add(job)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
