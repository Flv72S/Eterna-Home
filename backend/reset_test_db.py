import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurazione del database
DB_NAME = "eterna_home_test"
DB_USER = "postgres"
DB_PASSWORD = "N0nn0c4rl0!!"
DB_HOST = "localhost"

def reset_test_database():
    """Resetta il database di test."""
    try:
        # Connessione al database postgres
        logger.debug("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Chiudi tutte le connessioni al database di test
        logger.debug(f"Closing all connections to {DB_NAME}...")
        cur.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        
        # Elimina il database se esiste
        logger.debug(f"Dropping database {DB_NAME} if it exists...")
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        
        # Crea il database
        logger.debug(f"Creating database {DB_NAME}...")
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        
        cur.close()
        conn.close()
        logger.debug("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise

if __name__ == "__main__":
    reset_test_database() 