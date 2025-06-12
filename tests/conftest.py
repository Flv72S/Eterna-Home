"""Configurazione dei test."""
import os
import pytest
import logging
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.core.config import settings
from app.core.security import get_password_hash

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Importa la configurazione Redis per i test
from tests.conftest_redis import redis_client, override_redis_settings

# Configurazione del database di test
TEST_DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"
TEST_DATABASE_NAME = "eterna_home_test"

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Crea il database di test se non esiste."""
    logger.debug("Setting up test database...")
    try:
        # Connessione al database postgres
        logger.debug("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="N0nn0c4rl0!!",
            host="localhost"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Verifica se il database esiste
        logger.debug(f"Checking if database {TEST_DATABASE_NAME} exists...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DATABASE_NAME,))
        exists = cur.fetchone()
        
        if not exists:
            logger.debug(f"Creating test database {TEST_DATABASE_NAME}...")
            cur.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
            logger.debug("Test database created successfully")
        else:
            logger.debug(f"Test database {TEST_DATABASE_NAME} already exists")
        
        # Verifica la connessione al database di test
        logger.debug("Testing connection to test database...")
        cur.close()
        conn.close()
        
        test_conn = psycopg2.connect(
            dbname=TEST_DATABASE_NAME,
            user="postgres",
            password="N0nn0c4rl0!!",
            host="localhost"
        )
        test_conn.close()
        logger.debug("Successfully connected to test database")
        
        yield
        
    except Exception as e:
        logger.error(f"Error setting up test database: {str(e)}")
        import traceback
        logger.error(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
        raise

@pytest.fixture(scope="session")
def test_engine():
    """Crea un engine PostgreSQL per i test."""
    logger.debug("Creating test engine...")
    try:
        engine = create_engine(
            TEST_DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=True  # Abilita il logging SQL
        )
        logger.debug("Test engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error creating test engine: {str(e)}")
        raise

@pytest.fixture(scope="session")
def test_db_session(test_engine):
    """Crea una sessione di test."""
    logger.debug("Creating test database session...")
    try:
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        session = TestingSessionLocal()
        logger.debug("Test database session created successfully")
        try:
            yield session
        finally:
            session.close()
            logger.debug("Test database session closed")
    except Exception as e:
        logger.error(f"Error creating test database session: {str(e)}")
        raise

@pytest.fixture(scope="session", autouse=True)
def create_test_db(test_engine):
    """Crea le tabelle nel database di test."""
    logger.debug("Creating test database tables...")
    try:
        SQLModel.metadata.create_all(test_engine)
        logger.debug("Test database tables created successfully")
        yield
        # Pulizia: elimina tutte le tabelle dal database di test in ordine corretto
        with test_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS document_versions CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS maintenance_records CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS nodes CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS rooms CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS houses CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS bookings CASCADE"))
            conn.commit()
        logger.debug("Test database tables dropped")
    except Exception as e:
        logger.error(f"Error creating test database tables: {str(e)}")
        raise

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Crea una sessione di test e la pulisce dopo ogni test."""
    logger.debug("Creating function-scoped test session...")
    try:
        with Session(test_engine) as session:
            yield session
            session.rollback()
            logger.debug("Function-scoped test session rolled back")
    except Exception as e:
        logger.error(f"Error in function-scoped test session: {str(e)}")
        raise

@pytest.fixture(name="session")
def session_fixture(test_engine):
    """Fixture per creare una sessione di test."""
    logger.debug("Creating session fixture...")
    try:
        with Session(test_engine) as session:
            yield session
            logger.debug("Session fixture completed")
    except Exception as e:
        logger.error(f"Error in session fixture: {str(e)}")
        raise

@pytest.fixture(autouse=True)
def override_get_session(session: Session):
    """Override della funzione get_session per i test."""
    logger.debug("Overriding get_session for tests...")
    def _get_session():
        yield session
    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.clear()
    logger.debug("get_session override cleared")

@pytest.fixture(name="client")
def test_client():
    """Crea un test client con la sessione di test già configurata."""
    logger.debug("Creating test client...")
    with TestClient(app) as client:
        yield client
        logger.debug("Test client closed")

@pytest.fixture(name="document_table")
def create_document_table(db_session):
    """Assicura che la tabella document esista e sia pulita dopo ogni test."""
    logger.debug("Creating document table...")
    SQLModel.metadata.create_all(test_engine, tables=[Document.__table__])
    yield db_session
    logger.debug("Document table fixture completed")

@pytest.fixture(scope="function")
def test_user(db_session):
    """Crea un utente di test."""
    logger.debug("Creating test user...")
    try:
        # Svuota completamente la tabella users
        logger.debug("Truncating users table...")
        db_session.execute(text("TRUNCATE TABLE users CASCADE"))
        db_session.commit()
        logger.debug("Users table truncated successfully")
        
        logger.debug("Creating new test user...")
        user = User(
            email="testuser@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_superuser=False
        )
        logger.debug("Adding user to session...")
        db_session.add(user)
        logger.debug("Committing user to database...")
        db_session.commit()
        logger.debug("Refreshing user from database...")
        db_session.refresh(user)
        logger.debug(f"Test user created with ID: {user.id}")
        logger.debug(f"User hashed password: {user.hashed_password}")
        return user
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        import traceback
        logger.error(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
        raise

@pytest.fixture(scope="function")
def test_document(db_session, test_user):
    """Crea un documento di test."""
    logger.debug("Creating test document...")
    try:
        document = Document(
            title="Test Document",
            description="A test document",
            owner_id=test_user.id,
            name="manuale_test.pdf",
            type="application/pdf",
            size=12345,
            upload_date=datetime.now(timezone.utc),
            path="/documents/manuali/manuale_test.pdf",
            checksum="abc123",
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        logger.debug(f"Test document created with ID: {document.id}")
        return document
    except Exception as e:
        logger.error(f"Error creating test document: {str(e)}")
        raise 