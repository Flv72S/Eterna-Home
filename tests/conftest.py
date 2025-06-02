import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app

@pytest.fixture(name="db")
def db_session():
    """Create a fresh database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(autouse=True)
def override_get_session(db):
    app.dependency_overrides[get_session] = lambda: db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(name="client")
def test_client(db: Session):
    """Create a test client with a fresh database."""
    def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear() 