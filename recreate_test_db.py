import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def recreate_test_database():
    """Ricrea il database di test da zero"""
    try:
        # Connessione al database postgres
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='N0nn0c4rl0!!',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Termina tutte le connessioni al database di test
        logger.info("Terminazione connessioni al database di test...")
        cur.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'eterna_home_test'
            AND pid <> pg_backend_pid();
        """)
        
        # Elimina il database se esiste
        logger.info("Eliminazione database di test se esistente...")
        cur.execute("DROP DATABASE IF EXISTS eterna_home_test;")
        
        # Crea il nuovo database
        logger.info("Creazione nuovo database di test...")
        cur.execute("CREATE DATABASE eterna_home_test;")
        
        cur.close()
        conn.close()
        
        logger.info("Database di test ricreato con successo!")
        
    except Exception as e:
        logger.error(f"Errore durante la ricreazione del database: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_test_database() 