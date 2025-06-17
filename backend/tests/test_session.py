from sqlmodel import SQLModel, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crea il motore per il database di test
test_engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Crea la sessione di test
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

# Funzione per ottenere una sessione di test
def get_test_session():
    with TestSessionLocal() as session:
        yield session 