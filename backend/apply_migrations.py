from alembic.config import Config
from alembic import command
import logging

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def apply_migrations():
    """Applica le migrazioni Alembic al database di test."""
    try:
        # Configura Alembic
        logger.debug("Configuring Alembic...")
        alembic_cfg = Config("alembic.ini")
        
        # Applica tutte le migrazioni
        logger.debug("Applying migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.debug("Migrations applied successfully")
        
    except Exception as e:
        logger.error(f"Error applying migrations: {str(e)}")
        raise

if __name__ == "__main__":
    apply_migrations() 