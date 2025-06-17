import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database():
    # Connessione al database postgres per poter eliminare e ricreare il database
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='N0nn0c4rl0!!',
        host='localhost',
        port='5432'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Chiudi tutte le connessioni al database
    cur.execute("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'eterna_home_test'
        AND pid <> pg_backend_pid();
    """)

    # Elimina il database se esiste
    cur.execute('DROP DATABASE IF EXISTS eterna_home_test')
    print("Database eliminato")

    # Crea il database
    cur.execute('CREATE DATABASE eterna_home_test')
    print("Database creato")

    cur.close()
    conn.close()

if __name__ == '__main__':
    reset_database() 