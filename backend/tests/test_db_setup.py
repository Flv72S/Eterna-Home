import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Configurazione database di test
DATABASE_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database_connection():
    """Verifica che la connessione al database funzioni."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Connessione al database fallita: {str(e)}")

def test_database_tables():
    """Verifica che le tabelle necessarie esistano."""
    try:
        with engine.connect() as conn:
            # Verifica tabella nodes
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'nodes')"))
            assert result.scalar() is True, "Tabella 'nodes' non trovata"
            
            # Verifica tabella maintenance_records
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'maintenance_records')"))
            assert result.scalar() is True, "Tabella 'maintenance_records' non trovata"
    except Exception as e:
        pytest.fail(f"Verifica tabelle fallita: {str(e)}")

def test_database_migrations():
    """Verifica che le migrazioni siano state applicate."""
    try:
        with engine.connect() as conn:
            # Verifica tabella alembic_version
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"))
            assert result.scalar() is True, "Tabella 'alembic_version' non trovata"
            
            # Verifica che ci sia almeno una versione
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            assert version is not None, "Nessuna versione di migrazione trovata"
    except Exception as e:
        pytest.fail(f"Verifica migrazioni fallita: {str(e)}") 