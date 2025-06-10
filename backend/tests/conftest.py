import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from pytest_alembic import create_alembic_fixture

# Aggiungi la directory root del progetto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Forza l'uso del database di test durante i test
os.environ["TESTING"] = "1"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "N0nn0c4rl0!!"
os.environ["POSTGRES_DB"] = "eterna_home_test"
os.environ["DATABASE_URL"] = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

# Importa app dopo aver aggiunto il percorso
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from tests.utils import get_superuser_token_headers
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

# Database di test
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_database():
    """Create test database if it doesn't exist."""
    # Connessione al database postgres per creare il database di test
    postgres_engine = create_engine("postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres")
    with postgres_engine.connect() as conn:
        # Termina tutte le connessioni al database di test
        conn.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'eterna_home_test'
            AND pid <> pg_backend_pid();
        """))
        conn.execute(text("COMMIT"))  # Chiudi eventuali transazioni pendenti
        conn.execute(text(f"DROP DATABASE IF EXISTS eterna_home_test"))
        conn.execute(text(f"CREATE DATABASE eterna_home_test"))
    postgres_engine.dispose()

def drop_test_database():
    """Drop test database."""
    # Connessione al database postgres per eliminare il database di test
    postgres_engine = create_engine("postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres")
    with postgres_engine.connect() as conn:
        # Termina tutte le connessioni al database di test
        conn.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'eterna_home_test'
            AND pid <> pg_backend_pid();
        """))
        conn.execute(text("COMMIT"))  # Chiudi eventuali transazioni pendenti
        conn.execute(text(f"DROP DATABASE IF EXISTS eterna_home_test"))
    postgres_engine.dispose()

def drop_all_tables():
    """Drop all tables in the database."""
    inspector = inspect(engine)
    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            if table_name != 'alembic_version':  # Non eliminare la tabella alembic_version
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        conn.commit()

def apply_migrations():
    from alembic.config import Config
    from alembic import command
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    command.upgrade(config, "head")

def create_superuser(db: TestingSessionLocal):
    from app.models.user import User
    from app.core.config import settings
    from app.core.security import get_password_hash

    user = db.query(User).filter(
        (User.email == settings.FIRST_SUPERUSER_EMAIL) |
        (User.username == settings.FIRST_SUPERUSER)
    ).first()
    if user:
        return user
    user = User(
        email=settings.FIRST_SUPERUSER_EMAIL,
        username=settings.FIRST_SUPERUSER,
        hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
        is_superuser=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database before running tests and drop it after."""
    create_test_database()
    apply_migrations()
    yield
    # Chiudi tutte le connessioni al database prima di eliminarlo
    engine.dispose()
    drop_test_database()

# Configurazione di Alembic per i test
@pytest.fixture(scope="session")
def alembic_config():
    """Configura Alembic per usare il database di test."""
    from alembic.config import Config
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    return config

@pytest.fixture(scope="session")
def alembic_engine():
    """Fornisce l'engine di Alembic per i test."""
    return engine

# Crea il fixture per alembic
alembic_runner = create_alembic_fixture()

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def db_engine():
    """Fixture che fornisce l'engine del database per i test."""
    return engine

@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient, db: TestingSessionLocal) -> dict:
    """Fixture che fornisce gli header di autenticazione per un utente superuser."""
    create_superuser(db)
    return get_superuser_token_headers(client) 