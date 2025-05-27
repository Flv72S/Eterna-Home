import logging
import sys
import os
from datetime import datetime

def setup_logging():
    # Crea la directory dei log se non esiste
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configura il logger root
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                encoding='utf-8'
            )
        ]
    )

    # Configura il logger per SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    
    # Configura il logger per FastAPI
    logging.getLogger('fastapi').setLevel(logging.DEBUG)
    
    # Configura il logger per Uvicorn
    logging.getLogger('uvicorn').setLevel(logging.DEBUG)
    logging.getLogger('uvicorn.access').setLevel(logging.DEBUG)
    logging.getLogger('uvicorn.error').setLevel(logging.DEBUG)
    
    # Configura il logger per il nostro codice
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    
    # Aggiungi un handler per il file di log
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'main_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(message)s'
    ))
    logger.addHandler(file_handler)

    # Configura il logger per MinIO
    logging.getLogger('minio').setLevel(logging.DEBUG)
    
    # Configura il logger per il nostro codice
    logging.getLogger('routers').setLevel(logging.DEBUG)
    logging.getLogger('utils').setLevel(logging.DEBUG)
    
    # Configura il logger per il traceback
    logging.getLogger('traceback').setLevel(logging.DEBUG) 