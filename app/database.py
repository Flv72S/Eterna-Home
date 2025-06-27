from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.models.room import Room
from app.models.booking import Booking
from app.models.audio_log import AudioLog
import logging

logger = logging.getLogger(__name__)

def get_engine():
    """Crea l'engine del database con configurazioni di sicurezza."""
    # Configurazione SSL per PostgreSQL
    connect_args = {}
    
    if settings.DATABASE_SSL_MODE and settings.DATABASE_SSL_MODE != "disable":
        connect_args["sslmode"] = settings.DATABASE_SSL_MODE
        logger.info(f"Database SSL mode: {settings.DATABASE_SSL_MODE}")
    
    return create_engine(
        settings.DATABASE_URL, 
        pool_pre_ping=True, 
        pool_size=5, 
        max_overflow=10, 
        echo=True,
        connect_args=connect_args
    )

engine = get_engine()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

get_db = get_session 