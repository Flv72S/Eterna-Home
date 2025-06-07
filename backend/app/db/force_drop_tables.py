from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("SET session_replication_role = 'replica';"))
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """))
    tables = [row[0] for row in result]
    print(f"Tabelle trovate: {tables}")
    for table in tables:
        try:
            print(f"Elimino tabella: {table}")
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        except Exception as e:
            print(f"Errore durante l'eliminazione della tabella {table}: {e}")
    conn.execute(text("SET session_replication_role = 'origin';"))
    conn.commit()
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """))
    tables = [row[0] for row in result]
    print(f"Tabelle rimaste dopo la cancellazione: {tables}")

print("Reset completato.") 