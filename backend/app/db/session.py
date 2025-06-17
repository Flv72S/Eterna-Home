from sqlmodel import SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Determina se siamo in modalità test
is_test = os.getenv("TESTING", "false").lower() == "true"

# Crea il motore per PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Impostiamo echo direttamente a True
    future=True,
    pool_pre_ping=True,
    pool_recycle=300
)

# Crea la sessione
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Funzione per ottenere una sessione del database
def get_session():
    with SessionLocal() as session:
        yield session 