from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import text
import datetime

# Configurazione del database
DATABASE_URL = 'postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home'

def create_users_table():
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Definizione della tabella users
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('username', String(50), unique=True, nullable=False),
        Column('email', String(100), unique=True, nullable=False),
        Column('hashed_password', String(100), nullable=False),
        Column('full_name', String(100), nullable=True),
        Column('phone_number', String(20), nullable=True),
        Column('is_active', Boolean, nullable=False, default=True),
        Column('is_superuser', Boolean, nullable=False, default=False),
        Column('is_verified', Boolean, nullable=False, default=False),
        Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
        Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
        Column('last_login', DateTime, nullable=True)
    )
    
    try:
        # Crea la tabella
        metadata.create_all(engine)
        print("Tabella users creata con successo!")
        
        # Verifica che la tabella esista
        with engine.connect() as conn:
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"))
            exists = result.scalar()
            print(f"Verifica: La tabella users esiste: {exists}")
            
    except Exception as e:
        print(f"Errore durante la creazione della tabella: {str(e)}")

if __name__ == '__main__':
    create_users_table() 