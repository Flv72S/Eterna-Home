import logging
import os
from pathlib import Path

# Crea la directory logs se non esiste
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurazione del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output su console
        logging.FileHandler("logs/app.log")  # Output su file
    ]
)

# Crea il logger
logger = logging.getLogger("eterna_home")

# Esempio di utilizzo:
# logger.info("Messaggio informativo")
# logger.error("Messaggio di errore")
# logger.debug("Messaggio di debug")
