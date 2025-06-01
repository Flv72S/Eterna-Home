from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Crea la tabella users direttamente
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
    
    # Crea gli indici
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
    """))
    
    # Crea la tabella alembic_version con vincolo di unicità
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
    """))
    
    # Inserisce la versione corrente
    conn.execute(text("""
        INSERT INTO alembic_version (version_num) 
        VALUES ('create_users_table')
        ON CONFLICT (version_num) DO NOTHING;
    """))
    
    conn.commit()
    print("Migration forzata completata con successo.") 