import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document

# Create a test engine
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Crea tutte le tabelle all'inizio dei test e le pulisce alla fine."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Crea una sessione di test e la pulisce dopo ogni test."""
    with Session(test_engine) as session:
        yield session
        session.rollback()

@pytest.fixture(scope="function", autouse=True)
def override_get_session(db_session):
    """Override la dependency get_session per usare sempre la sessione di test."""
    def _override_get_session():
        yield db_session
    
    app.dependency_overrides[get_session] = _override_get_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(name="client")
def test_client():
    """Crea un test client con la sessione di test già configurata."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(name="document_table")
def create_document_table(db_session):
    """Assicura che la tabella document esista e sia pulita dopo ogni test."""
    SQLModel.metadata.create_all(test_engine, tables=[Document.__table__])
    yield db_session
    # Non è necessario pulire la tabella qui perché viene gestita da create_test_db 