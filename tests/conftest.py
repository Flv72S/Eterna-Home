"""Configurazione dei test."""
import os
import pytest
import logging
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.pool import StaticPool
from app.core.redis import get_redis_client
import redis
from fakeredis import FakeRedis
# [DISABILITATO TEMPORANEAMENTE: Alembic]
# from alembic.config import Config
# from alembic import command

# Aggiungi il path del progetto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disabilita il rate limiting per i test
os.environ["ENABLE_RATE_LIMITING"] = "false"
os.environ["RATE_LIMIT_REQUESTS"] = "1000"
os.environ["RATE_LIMIT_WINDOW"] = "60"

# Imposta l'ambiente di test per disabilitare la cache degli utenti
os.environ["ENVIRONMENT"] = "test"

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
from app.models.bim_model import BIMModel
from app.models.room import Room
from app.models.booking import Booking
from app.models.document_version import DocumentVersion
from app.models.user_tenant_role import UserTenantRole
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user_house import UserHouse

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
            cleanup_session.execute(text("DELETE FROM user_tenant_roles"))
            cleanup_session.execute(text("DELETE FROM role_permissions"))
            cleanup_session.execute(text("DELETE FROM roles"))
            cleanup_session.execute(text("DELETE FROM maintenance_records"))
            cleanup_session.execute(text("DELETE FROM bookings"))
            cleanup_session.execute(text("DELETE FROM rooms"))
            cleanup_session.execute(text("DELETE FROM nodes"))
            cleanup_session.execute(text("DELETE FROM documents"))
            cleanup_session.execute(text("DELETE FROM document_versions"))
            cleanup_session.execute(text("DELETE FROM bim_models"))
            cleanup_session.execute(text("DELETE FROM user_houses"))
            cleanup_session.execute(text("DELETE FROM user_tenant_roles"))
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
    """Client di test per autenticazione con sessione persistente."""
    def _get_session():
        with Session(engine) as session:
            yield session
            # NON fare rollback automatico - lascia i dati nel database per l'autenticazione
    
    app.dependency_overrides[get_session] = _get_session
    from app.main import app
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def create_test_user(session):
    """Crea un utente di test nel database."""
    from app.models.user import User
    from app.utils.password import get_password_hash
    import time
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
    """Sessione di test per autenticazione senza rollback automatico."""
    session = Session(engine)
    yield session
    session.close()

@pytest.fixture(scope="function")
def test_user_auth(auth_test_session):
    """Utente di test per autenticazione con sessione persistente."""
    user = create_test_user(auth_test_session)
    yield user
    # Non fare rollback - lascia l'utente nel database per i test di autenticazione

@pytest.fixture(scope="function")
def test_user_shared_session(db_session):
    """Utente di test con sessione condivisa per test generali."""
    user = create_test_user(db_session)
    yield user
    # Il rollback viene gestito dalla fixture db_session

@pytest.fixture(scope="function")
def test_user(db_session):
    """Utente di test standard."""
    from app.models.user import User
    from app.utils.password import get_password_hash
    import time
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
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Il rollback viene gestito dalla fixture db_session

@pytest.fixture(scope="function")
def test_document(db_session, test_user):
    """Documento di test."""
    from app.models.document import Document
    from app.models.house import House
    import time
    timestamp = int(time.time() * 1000)
    
    # Crea una casa di test
    house = House(
        name=f"Test House {timestamp}",
        address="Test Address",
        description="Test Description"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea un documento di test
    document = Document(
        filename=f"test_document_{timestamp}.pdf",
        original_filename=f"test_document_{timestamp}.pdf",
        file_path=f"/test/path/test_document_{timestamp}.pdf",
        file_size=1024,
        mime_type="application/pdf",
        uploaded_by=test_user.id,
        house_id=house.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    yield document
    # Il rollback viene gestito dalla fixture db_session

@pytest.fixture
def test_token():
    """Token di test per autenticazione."""
    return create_access_token(data={"sub": "test@example.com"})

@pytest.fixture
def auth_headers(test_token):
    """Headers di autenticazione per i test."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def reset_rate_limiting():
    """Reset del rate limiting per i test."""
    if redis_client:
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

@pytest.fixture(autouse=True, scope="function")
def mock_rate_limiting():
    """Mock globale per disabilitare il rate limiting in tutti i test."""
    from unittest.mock import patch, MagicMock
    from app.security.limiter import security_limiter
    
    # Crea un mock del limiter che non applica mai limiti
    mock_limiter = MagicMock()
    mock_limiter.hit.return_value = (True, 1000, 1000, 60)  # Sempre successo
    mock_limiter.get_window_stats.return_value = (0, 1000, 60)  # Sempre sotto il limite
    mock_limiter.limit.return_value = lambda func: func  # Decoratore che non fa nulla
    
    with patch("app.security.limiter.security_limiter.limiter", mock_limiter):
        with patch("app.security.limiter.settings.ENABLE_RATE_LIMITING", False):
            yield

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
        
        # Mock per presigned URLs
        instance.presigned_get_object.return_value = "https://mocked-minio.com/presigned-url"
        instance.presigned_put_object.return_value = "https://mocked-minio.com/presigned-upload-url"
        
        # Mock per list objects
        mock_object = MagicMock()
        mock_object.object_name = "test_file.pdf"
        mock_object.size = 12345
        mock_object.last_modified = datetime.now()
        instance.list_objects.return_value = [mock_object]
        
        # Mock per bucket policy
        instance.set_bucket_policy.return_value = None
        instance.delete_bucket_policy.return_value = None
        
        # Mock per stat object
        mock_stat = MagicMock()
        mock_stat.size = 12345
        mock_stat.last_modified = datetime.now()
        mock_stat.content_type = "application/pdf"
        instance.stat_object.return_value = mock_stat
        
        minio_mock.return_value = instance
        yield

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

def create_test_user_with_permissions(session, permissions: list):
    """
    Crea un utente di test e gli assegna i permessi specificati (come stringhe).
    """
    from app.models.user import User
    from app.models.permission import Permission
    from app.models.user_permission import UserPermission
    from app.utils.password import get_password_hash
    import time
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
    # Assegna permessi
    for perm_name in permissions:
        perm = session.exec(select(Permission).where(Permission.name == perm_name)).first()
        if not perm:
            perm = Permission(name=perm_name, description=f"Permesso test: {perm_name}")
            session.add(perm)
            session.commit()
            session.refresh(perm)
        user_perm = UserPermission(user_id=user.id, permission_id=perm.id)
        session.add(user_perm)
    session.commit()
    return user