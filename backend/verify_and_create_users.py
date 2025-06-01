from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Mostra il database corrente
    current_db = conn.execute(text('SELECT current_database()')).scalar()
    print(f"Database corrente: {current_db}")
    
    # Verifica se la tabella users esiste
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)).scalar()
    print(f"La tabella users esiste prima della creazione: {result}")
    
    # Crea la tabella users se non esiste
    if not result:
        print("Creazione della tabella users...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                phone_number VARCHAR(20),
                is_active BOOLEAN NOT NULL DEFAULT true,
                is_superuser BOOLEAN NOT NULL DEFAULT false,
                is_verified BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """))
        print("Tabella users creata.")
    
    # Verifica se la tabella users esiste dopo la creazione
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)).scalar()
    print(f"La tabella users esiste dopo la creazione: {result}") 