from sqlalchemy import create_engine, text

# Connessione al database postgres (default) per droppare/ricreare eterna_home_test
DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres'
engine = create_engine(DATABASE_URL)

with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    # Termina tutte le connessioni al database eterna_home_test
    conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'eterna_home_test'"))
    # Droppa il database se esiste
    conn.execute(text('DROP DATABASE IF EXISTS eterna_home_test'))
    # Ricrea il database
    conn.execute(text('CREATE DATABASE eterna_home_test'))
    print('Database eterna_home_test ricreato con successo.') 