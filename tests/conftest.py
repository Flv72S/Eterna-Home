"""Configurazione dei test."""
import os
import pytest
import logging
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.pool import StaticPool
from app.core.redis import get_redis_client
import redis
from fakeredis import FakeRedis
# [DISABILITATO TEMPORANEAMENTE: Alembic]
# from alembic.config import Config
# from alembic import command

from app.database import get_session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.core.config import settings
from app.core.security import get_password_hash
from app.services.minio_service import get_minio_service

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Importa la configurazione Redis per i test
from tests.conftest_redis import redis_client, override_redis_client

# Configurazione del database di test
TEST_DATABASE_URL = settings.DATABASE_URL
TEST_DATABASE_NAME = "eterna_home_test"

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Si assicura che il database di test esista. Le migrazioni e la preparazione sono demandate a script esterno (reset_and_seed.py)."""
    logger.debug("[TEST] Assicurazione esistenza test DB: nessun drop/creazione/migrazione, demandato a script esterno.")
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname=TEST_DATABASE_NAME,
            user="postgres",
            password="N0nn0c4rl0!!",
            host="localhost"
        )
        conn.close()
    except Exception as e:
        raise RuntimeError(f"[TEST] Il database di test {TEST_DATABASE_NAME} non esiste o non è raggiungibile. Esegui prima reset_and_seed.py. Errore: {e}")

@pytest.fixture(scope="session")
def engine():
    from app.database import get_engine
    return get_engine()

@pytest.fixture(scope="function")
def db_session(engine):
    logger.debug("Creating function-scoped test session...")
    try:
        with Session(engine) as session:
            yield session
            session.rollback()
            logger.debug("Function-scoped test session rolled back")
    except Exception as e:
        logger.error(f"Error in function-scoped test session: {str(e)}")
        raise

@pytest.fixture(scope="function")
def session(engine):
    logger.debug("Creating session fixture...")
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        logger.debug("Session fixture completed")

@pytest.fixture(autouse=True)
def override_get_session(engine):
    def _get_session():
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(name="client")
def test_client(override_get_session):
    logger.debug("Creating test client...")
    from app.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client
        logger.debug("Test client closed")

@pytest.fixture(scope="function")
def test_user(db_session):
    """Crea un utente di test."""
    logger.debug("Creating test user...")
    try:
        user = User(
            email="testuser@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("TestPassword123!"),
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

@pytest.fixture
def test_token():
    """Fixture per ottenere un token di test fisso."""
    from app.core.config import settings
    return settings.TEST_TOKEN

@pytest.fixture
def auth_headers(test_token):
    """Fixture per ottenere headers di autenticazione con token fisso."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def reset_rate_limiting():
    """Fixture per resettare il rate limiting tra i test."""
    from app.core.redis import get_redis_client
    
    # Reset del rate limiting
    redis_client = get_redis_client()
    if redis_client:
        # Pulisce tutte le chiavi che potrebbero essere usate dal rate limiting
        # slowapi usa pattern come "slowapi:ratelimit:endpoint:key"
        keys_to_delete = []
        
        # Cerca chiavi con pattern slowapi
        slowapi_keys = redis_client.keys("slowapi:*")
        keys_to_delete.extend(slowapi_keys)
        
        # Cerca anche chiavi con pattern ratelimit
        ratelimit_keys = redis_client.keys("*ratelimit*")
        keys_to_delete.extend(ratelimit_keys)
        
        # Cerca chiavi con pattern testclient (usato nei test)
        testclient_keys = redis_client.keys("*testclient*")
        keys_to_delete.extend(testclient_keys)
        
        # Rimuovi duplicati
        keys_to_delete = list(set(keys_to_delete))
        
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
            print(f"Reset rate limiting: eliminate {len(keys_to_delete)} chiavi")
    
    yield
    
    # Cleanup dopo il test
    if redis_client:
        keys_to_delete = []
        slowapi_keys = redis_client.keys("slowapi:*")
        keys_to_delete.extend(slowapi_keys)
        ratelimit_keys = redis_client.keys("*ratelimit*")
        keys_to_delete.extend(ratelimit_keys)
        testclient_keys = redis_client.keys("*testclient*")
        keys_to_delete.extend(testclient_keys)
        keys_to_delete = list(set(keys_to_delete))
        
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)

@pytest.fixture
def mock_minio_service():
    """Mock del servizio MinIO per i test."""
    mock_service = Mock()
    
    # Mock dei metodi principali
    mock_service.upload_file.return_value = True
    mock_service.get_presigned_get_url.return_value = "https://mock-minio.com/test-file.pdf"
    mock_service.get_presigned_put_url.return_value = "https://mock-minio.com/upload-url"
    mock_service.delete_file.return_value = True
    mock_service.file_exists.return_value = True
    
    return mock_service

@pytest.fixture
def override_minio_service(mock_minio_service):
    """Override del servizio MinIO con mock per i test."""
    def _get_mock_minio_service():
        return mock_minio_service
    
    app.dependency_overrides[get_minio_service] = _get_mock_minio_service
    yield
    app.dependency_overrides.pop(get_minio_service, None)