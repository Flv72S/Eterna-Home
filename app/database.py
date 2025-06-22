from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.models.room import Room
from app.models.booking import Booking

def get_engine():
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10, echo=True)

engine = get_engine()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

get_db = get_session