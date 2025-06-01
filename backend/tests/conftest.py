import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from pytest_alembic import create_alembic_fixture

# Aggiungi la directory root del progetto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importa app dopo aver aggiunto il percorso
from app.main import app
from app.db.session import Base, get_db

# Database di test
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crea il fixture per alembic
alembic_runner = create_alembic_fixture()

def drop_all_tables():
    """Drop all tables in the database."""
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        if table_name != 'alembic_version':  # Non eliminare la tabella alembic_version
            engine.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Drop all tables before the test
    drop_all_tables()
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test
        drop_all_tables()

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

@pytest.fixture(autouse=True)
def setup_test_database(db_engine):
    """Fixture che prepara il database per i test."""
    # Drop all tables before the test
    drop_all_tables()
    yield
    # Drop all tables after the test
    drop_all_tables() 