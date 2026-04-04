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
    # Seed test dataset
    from app.services.pipeline import seed_jobs
    db = TestingSessionLocal()
    seed_jobs(db, 50)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
