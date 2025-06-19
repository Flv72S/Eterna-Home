import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configurazione del database
DB_NAME = "eterna_home_test"
DB_USER = "postgres"
DB_PASSWORD = "N0nn0c4rl0!!"
DB_HOST = "localhost"

def reset_database():
    # Connessione al database postgres
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Chiudi tutte le connessioni al database
    cur.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{DB_NAME}'
        AND pid <> pg_backend_pid();
    """)
    
    # Elimina il database se esiste
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    print(f"Database {DB_NAME} eliminato se esisteva")
    
    # Crea il nuovo database
    cur.execute(f"CREATE DATABASE {DB_NAME}")
    print(f"Database {DB_NAME} creato")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    reset_database() 