from sqlmodel import SQLModel, select, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Importa qui tutti i modelli per assicurarti che siano registrati con SQLModel
from app.models.user import User

# Crea il motore per PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Crea la sessione
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Crea tutte le tabelle
def create_tables():
    SQLModel.metadata.create_all(engine)

# Funzione per ottenere una sessione del database
def get_session():
    with SessionLocal() as session:
        yield session 