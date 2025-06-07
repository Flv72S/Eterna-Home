from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """))
    tables = [row[0] for row in result]
    print(f"Tabelle presenti nel database: {tables}") 