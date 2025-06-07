from alembic.config import Config
from alembic import command
import os

# Imposta l'ambiente di test
os.environ["TESTING"] = "1"

# Configura Alembic
config = Config('alembic.ini')

# Applica la migrazione
command.upgrade(config, 'head')

print('Migrazione applicata con successo') 