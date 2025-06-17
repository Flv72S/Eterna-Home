from sqlmodel import create_engine, Session, select
from app.core.config import settings
from app.models.user import User
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_test_database():
    """Verifica lo stato del database di test"""
    try:
        # Crea l'engine per il database di test
        engine = create_engine(settings.TEST_DATABASE_URL, echo=True)
        
        # Verifica la connessione
        with Session(engine) as session:
            # Conta gli utenti
            statement = select(User)
            users = session.exec(statement).all()
            logger.info(f"Numero di utenti nel database: {len(users)}")
            
            # Mostra i dettagli degli utenti
            for user in users:
                logger.info(f"Utente: id={user.id}, email={user.email}, username={user.username}")
                
        logger.info("Verifica database completata con successo")
        
    except Exception as e:
        logger.error(f"Errore durante la verifica del database: {str(e)}")
        raise

if __name__ == "__main__":
    check_test_database() 