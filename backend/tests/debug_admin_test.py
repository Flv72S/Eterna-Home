import sys
import os
import logging
from pathlib import Path

# Aggiungi la directory backend al path di Python
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_admin_test():
    """Script di debug per il test di creazione utente admin"""
    try:
        # 1. Verifica configurazione
        logger.info("=== Verifica configurazione ===")
        logger.info(f"API_V1_STR: {settings.API_V1_STR}")
        logger.info(f"DATABASE_URL: {settings.DATABASE_URL}")
        
        # 2. Verifica app FastAPI
        logger.info("\n=== Verifica app FastAPI ===")
        client = TestClient(app)
        logger.info("Routes disponibili:")
        for route in app.routes:
            logger.info(f"  {route.path} [{route.methods}]")
        
        # 3. Test endpoint di registrazione
        logger.info("\n=== Test endpoint di registrazione ===")
        admin_data = {
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User",
            "is_active": True,
            "is_superuser": True
        }
        
        # Verifica URL completo
        register_url = f"{settings.API_V1_STR}/auth/register"
        logger.info(f"Tentativo di chiamata a: {register_url}")
        
        # Esegui la chiamata e logga la risposta
        response = client.post(register_url, json=admin_data)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        # 4. Verifica errori comuni
        logger.info("\n=== Verifica errori comuni ===")
        if response.status_code == 404:
            logger.error("Endpoint non trovato. Verifica che il router sia incluso correttamente in app.main")
        elif response.status_code == 500:
            logger.error("Errore interno del server. Controlla i log del server per dettagli")
        
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Errore durante il debug: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = debug_admin_test()
    sys.exit(0 if success else 1)