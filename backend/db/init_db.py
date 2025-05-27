from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

from .session import Base, engine
from ..models.user import User
from ..models.house import House
from ..models.node import Node

logger = logging.getLogger(__name__)

def init_db():
    """Inizializza il database eliminando e ricreando tutte le tabelle"""
    try:
        # Elimina tutte le tabelle con CASCADE
        logger.info("Eliminazione di tutte le tabelle esistenti...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()
        
        logger.info("Creazione di tutte le tabelle...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database reinizializzato con successo!")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione del database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 