from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Verifica se la tabella users esiste
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)).scalar()
    
    print(f"La tabella users esiste: {result}")
    
    # Se esiste, mostra la sua struttura
    if result:
        columns = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'users'
            ORDER BY ordinal_position;
        """))
        
        print("\nStruttura della tabella users:")
        for col in columns:
            print(f"  - {col.column_name}: {col.data_type} (nullable: {col.is_nullable})") 