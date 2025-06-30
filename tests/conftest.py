"""Configurazione dei test."""
import os
import pytest
import logging
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
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
from app.models.role import Role
from app.models.user_role import UserRole
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.services.minio_service import get_minio_service

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Importa la configurazione Redis per i test
from tests.conftest_redis import redis_client, override_redis_client

# Configurazione del database di test
# Sovrascrive la configurazione per usare il database di test
os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"
# Disabilita Redis per i test se non configurato
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

TEST_DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"
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

@pytest.fixture(scope="session", autouse=True)
def create_tables(engine):
    """Crea automaticamente tutte le tabelle necessarie per i test."""
    logger.debug("[TEST] Creazione automatica delle tabelle per i test...")
    try:
        # Crea tutte le tabelle basate sui modelli SQLModel
        SQLModel.metadata.create_all(engine)
        logger.debug("[TEST] Tabelle create con successo")
    except Exception as e:
        logger.error(f"[TEST] Errore durante la creazione delle tabelle: {e}")
        raise

@pytest.fixture(autouse=True)
def clean_database(engine):
    """Pulisce automaticamente il database dopo ogni test."""
    yield
    # Cleanup dopo ogni test usando una sessione separata
    try:
        with Session(engine) as cleanup_session:
            # Elimina tutti i dati dalle tabelle in ordine inverso per rispettare le foreign key
            cleanup_session.execute(text("DELETE FROM user_roles"))
            cleanup_session.execute(text("DELETE FROM roles"))
            cleanup_session.execute(text("DELETE FROM maintenance_records"))
            cleanup_session.execute(text("DELETE FROM bookings"))
            cleanup_session.execute(text("DELETE FROM rooms"))
            cleanup_session.execute(text("DELETE FROM nodes"))
            cleanup_session.execute(text("DELETE FROM documents"))
            cleanup_session.execute(text("DELETE FROM document_versions"))
            cleanup_session.execute(text("DELETE FROM houses"))
            cleanup_session.execute(text("DELETE FROM users"))
            cleanup_session.commit()
            logger.debug("[TEST] Database pulito dopo il test")
    except Exception as e:
        logger.error(f"[TEST] Errore durante la pulizia del database: {e}")
        # Non facciamo rollback qui perché usiamo una sessione separata

@pytest.fixture(scope="session")
def engine():
    from sqlmodel import create_engine
    return create_engine(TEST_DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10, echo=True)

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

@pytest.fixture()
def override_get_session(engine):
    """Override della dipendenza get_session per i test."""
    # Crea una sessione persistente che non fa rollback automatico
    session = Session(engine)
    
    def _get_session():
        yield session
        # NON fare rollback automatico - lascia i dati nel database per l'autenticazione
    
    app.dependency_overrides[get_session] = _get_session
    yield
    # Cleanup alla fine del test
    session.close()
    app.dependency_overrides.clear()

@pytest.fixture()
def override_get_session_no_rollback(engine):
    """Fixture per test di autenticazione che non fa rollback automatico."""
    def _get_session():
        with Session(engine) as session:
            yield session
            # NON fare rollback automatico - lascia i dati nel database per l'autenticazione
    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def override_get_db(engine):
    def _get_db():
        with Session(engine) as session:
            yield session
    from app.core.deps import get_db
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(name="client")
def test_client(override_get_session, override_get_db):
    logger.debug("Creating test client...")
    from app.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client
        logger.debug("Test client closed")

@pytest.fixture(name="auth_client")
def auth_client(engine):
    from app.main import app
    from sqlmodel import Session
    session = Session(engine)
    def _get_session():
        yield session
    app.dependency_overrides[get_session] = _get_session
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client, session
    session.close()
    app.dependency_overrides.clear()

def create_test_user(session):
    import time
    from app.models.user import User
    from app.utils.password import get_password_hash
    timestamp = int(time.time() * 1000)
    user = User(
        email=f"testuser_{timestamp}@example.com",
        username=f"testuser_{timestamp}",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        role="guest",
        is_superuser=False,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_test_session(engine):
    """Sessione specifica per i test di autenticazione che non fa rollback automatico."""
    with Session(engine) as session:
        yield session
        # NON fare rollback - lascia i dati nel database per l'autenticazione

@pytest.fixture(scope="function")
def test_user_auth(auth_test_session):
    """Crea un utente di test usando la sessione di autenticazione."""
    import time
    logger.debug("Creating test user for auth...")
    try:
        # Usa timestamp per username unico
        timestamp = int(time.time() * 1000)
        username = f"testuser_{timestamp}"
        email = f"testuser_{timestamp}@example.com"
        
        user = User(
            email=email,
            username=username,
            full_name="Test User",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False
        )
        
        # Usa la stessa sessione che viene usata dall'app
        auth_test_session.add(user)
        auth_test_session.commit()
        auth_test_session.refresh(user)
        
        logger.debug(f"Test user created with ID: {user.id}")
        yield user
        
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise
    finally:
        # Cleanup: rimuovi l'utente dalla sessione
        try:
            if user and user.id:
                auth_test_session.delete(user)
                auth_test_session.commit()
        except Exception as e:
            logger.warning(f"Error cleaning up test user: {e}")

@pytest.fixture(scope="function")
def test_document(db_session, test_user):
    """Crea un documento di test."""
    logger.debug("Creating test document...")
    try:
        document = Document(
            name="Test Document",
            description="A test document",
            owner_id=test_user.id,
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

@pytest.fixture(autouse=True, scope="session")
def mock_minio():
    """Mock globale per MinIO in tutti i test."""
    with patch("app.services.minio_service.Minio") as minio_mock:
        instance = MagicMock()
        # Mock dei metodi principali
        instance.fput_object.return_value = None
        instance.get_object.return_value.read.return_value = b"mocked file content"
        instance.remove_object.return_value = None
        instance.bucket_exists.return_value = True
        instance.make_bucket.return_value = None
        minio_mock.return_value = instance
        yield

@pytest.fixture
def client():
    """Client di test per FastAPI"""
    return TestClient(app)

@pytest.fixture
def test_db():
    """Database di test in memoria"""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_user():
    """Utente admin per i test"""
    return {
        "id": 1,
        "email": "admin@test.com",
        "username": "admin",
        "is_active": True,
        "tenant_id": "house_123"
    }

@pytest.fixture
def regular_user():
    """Utente normale per i test"""
    return {
        "id": 2,
        "email": "user@test.com",
        "username": "user",
        "is_active": True,
        "tenant_id": "house_123"
    }

@pytest.fixture
def admin_token(admin_user):
    """Token JWT per utente admin"""
    return create_access_token(
        data={
            "sub": str(admin_user["id"]),
            "email": admin_user["email"],
            "tenant_id": admin_user["tenant_id"],
            "permissions": ["manage_users", "manage_roles", "manage_houses"]
        }
    )

@pytest.fixture
def regular_token(regular_user):
    """Token JWT per utente normale"""
    return create_access_token(
        data={
            "sub": str(regular_user["id"]),
            "email": regular_user["email"],
            "tenant_id": regular_user["tenant_id"],
            "permissions": ["read_own_data"]
        }
    )

@pytest.fixture
def mock_current_user():
    """Mock per get_current_user"""
    with patch('app.routers.admin.dashboard.get_current_user') as mock:
        yield mock

@pytest.fixture
def mock_db_session():
    """Mock per get_db"""
    with patch('app.routers.admin.dashboard.get_db') as mock:
        yield mock