from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Verifica se la tabella alembic_version esiste
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'alembic_version'
        );
    """)).scalar()
    
    print(f"La tabella alembic_version esiste: {result}")
    
    if result:
        # Se esiste, mostra il contenuto
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        if rows:
            print("Contenuto della tabella alembic_version:")
            for row in rows:
                print(f"  - {row.version_num}")
        else:
            print("La tabella alembic_version è vuota.")
    else:
        print("La tabella alembic_version non esiste nel database.") 