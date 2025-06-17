from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy import event
import logging
import time
from app.core.config import settings

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurazione dell'engine con timeout e pool settings
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Verifica la connessione prima di usarla
    pool_recycle=300,    # Ricicla le connessioni ogni 5 minuti
    pool_timeout=30,     # Timeout per ottenere una connessione dal pool
    max_overflow=10      # Numero massimo di connessioni in overflow
)

# Event listener per il logging delle query
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger.debug(f"Query eseguita in {total:.2f} secondi: {statement}")

def get_session():
    """Crea una nuova sessione di database."""
    start_time = time.time()
    try:
        session = Session(engine)
        logger.debug(f"Sessione creata in {time.time() - start_time:.2f} secondi")
        try:
            yield session
        finally:
            session.close()
            logger.debug(f"Sessione chiusa in {time.time() - start_time:.2f} secondi")
    except Exception as e:
        logger.error(f"Errore durante la creazione della sessione dopo {time.time() - start_time:.2f} secondi: {str(e)}")
        raise