# tests/conftest.py

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
# from alembic.config import Config
# from alembic import command
from app.core.config import settings
from tests.test_session import get_test_session

# URL del database di test
TEST_DATABASE_URL = settings.DATABASE_URL

def execute_sql_script(engine, script_path):
    """Esegue uno script SQL sul database."""
    if os.path.exists(script_path):
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with engine.connect() as conn:
            # Esegue ogni statement separatamente
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(text(statement))
                    except Exception as e:
                        print(f"[WARNING] Error executing SQL: {e}")
                        # Continua con gli altri statement
            conn.commit()
        print(f"[DEBUG] SQL script executed: {script_path}")
    else:
        print(f"[WARNING] SQL script not found: {script_path}")

@pytest.fixture(scope="session")
def test_engine():
    """Crea un engine di test."""
    print("\n[DEBUG] Creating test engine...")
    engine = create_engine(TEST_DATABASE_URL)
    print("[DEBUG] Test engine created successfully")
    return engine

@pytest.fixture
def db_session():
    """Crea una sessione di test."""
    for session in get_test_session():
        yield session

@pytest.fixture(scope="function", autouse=True)
def clean_db(test_engine):
    """Pulisce il database prima di ogni test e riapplica le migration."""
    print("\n[DEBUG] Cleaning database before test...")
    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    print("[DEBUG] Database cleaned")
    
    # Riapplica le migration dopo la pulizia
    print("[DEBUG] Reapplying migrations...")
    # alembic_cfg = Config("alembic.ini")
    # alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    # command.upgrade(alembic_cfg, "head")
    
    # Esegue lo script SQL per creare tutte le tabelle
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "create_all_tables.sql")
    execute_sql_script(test_engine, script_path)
    
    print("[DEBUG] Migrations reapplied")

@pytest.fixture(scope="session", autouse=True)
def create_test_db(test_engine):
    """Applica le migrazioni Alembic al database di test."""
    print("\n[DEBUG] Starting database setup...")

    # Pulizia: elimina tutte le tabelle dal database di test
    print("[DEBUG] Cleaning up database...")
    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    print("[DEBUG] Database cleanup completed")

    # Configura Alembic per usare il database di test
    print("[DEBUG] Configuring Alembic...")
    # alembic_cfg = Config("alembic.ini")
    # alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # Applica le migrazioni
    print("[DEBUG] Applying migrations...")
    # command.upgrade(alembic_cfg, "head")
    
    # Esegue lo script SQL per creare tutte le tabelle
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "create_all_tables.sql")
    execute_sql_script(test_engine, script_path)
    
    print("[DEBUG] Migrations applied successfully")

    yield

    # Pulizia finale
    print("[DEBUG] Final cleanup...")
    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    print("[DEBUG] Final cleanup completed")

@pytest.fixture
def client():
    """Crea un client di test."""
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)