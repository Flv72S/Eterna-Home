from typing import Generator
from sqlmodel import Session, create_engine
from app.core.config import settings

# Creazione dell'engine SQLModel
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.SQL_ECHO
)

def get_session() -> Generator[Session, None, None]:
    """
    Dependency per ottenere una sessione del database.
    
    Yields:
        Session: Sessione del database
    """
    with Session(engine) as session:
        yield session

