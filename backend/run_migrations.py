# [DISABILITATO TEMPORANEAMENTE: Alembic]
# Tutto il file disabilitato temporaneamente
from alembic.config import Config
from alembic import command
import os

# Configura l'URL del database di test
os.environ["DATABASE_URL"] = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"

# Crea la configurazione di Alembic
config = Config("alembic.ini")
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Esegui le migrazioni
command.upgrade(config, "head") 