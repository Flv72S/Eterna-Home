from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
import os

# Configurazione database
POSTGRES_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres"
TEST_DB_URL = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

def create_test_database():
    """Crea il database di test se non esiste."""
    # Connessione al database postgres per creare il database di test
    engine = create_engine(POSTGRES_URL)
    with engine.connect() as conn:
        # Termina tutte le connessioni al database di test
        conn.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'eterna_home_test'
            AND pid <> pg_backend_pid();
        """))
        conn.execute(text("COMMIT"))  # Chiudi eventuali transazioni pendenti
        conn.execute(text("DROP DATABASE IF EXISTS eterna_home_test"))
        conn.execute(text("CREATE DATABASE eterna_home_test"))
    engine.dispose()
    print("Database di test creato con successo.")

def apply_migrations():
    """Applica le migrazioni al database di test."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(config, "head")
    print("Migrazioni applicate con successo.")

if __name__ == "__main__":
    create_test_database()
    apply_migrations() 