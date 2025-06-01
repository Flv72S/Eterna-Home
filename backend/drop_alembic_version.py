from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Droppa la tabella alembic_version se esiste
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'alembic_version'
        );
    """)).scalar()
    if result:
        conn.execute(text("DROP TABLE alembic_version"))
        print("Tabella alembic_version droppata.")
    else:
        print("La tabella alembic_version non esiste.") 