from typing import Generator
from sqlmodel import Session, select, create_engine
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session 