from sqlmodel import SQLModel, create_engine, Session
from ..config.settings import settings

# Usa il DATABASE_URL dal file di configurazione
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")  # Debug print

# Crea l'engine per PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close() 