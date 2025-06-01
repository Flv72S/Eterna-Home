from sqlalchemy import create_engine, text

# Connessione al database eterna_home
engine = create_engine('postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home')

# Eliminazione della tabella alembic_version se esiste
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    conn.commit()
    print("Tabella alembic_version resettata con successo!") 