from sqlalchemy import create_engine, text

# Connessione al database postgres
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres')

# Usa AUTOCOMMIT per le operazioni sul database
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    # Chiudi tutte le connessioni al database eterna_home_test
    conn.execute(text("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'eterna_home_test'
        AND pid <> pg_backend_pid()
    """))

    # Elimina il database se esiste
    conn.execute(text('DROP DATABASE IF EXISTS eterna_home_test'))

    # Crea il database
    conn.execute(text('CREATE DATABASE eterna_home_test'))

print('Database eterna_home_test ricreato con successo') 