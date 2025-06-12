# tests/conftest.py

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from alembic.config import Config
from alembic import command
from app.core.config import settings

# Configurazione del database di test
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"
)

@pytest.fixture(scope="session")
def test_engine():
    """Crea un engine PostgreSQL per i test."""
    engine = create_engine(TEST_DATABASE_URL)
    return engine

@pytest.fixture(scope="session")
def test_db_session(test_engine):
    """Crea una sessione di test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session", autouse=True)
def create_test_db(test_engine):
    """Applica le migrazioni Alembic al database di test."""
    # Configura Alembic per usare il database di test
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    
    # Applica le migrazioni
    command.upgrade(alembic_cfg, "head")
    
    yield
    
    # Pulizia: elimina tutte le tabelle dal database di test
    SQLModel.metadata.drop_all(test_engine)