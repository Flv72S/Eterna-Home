from alembic.config import Config
from alembic import command

# Configura Alembic
config = Config('alembic.ini')

# Genera la migrazione
command.revision(config, message='initial_structure', autogenerate=True)

print('Migrazione iniziale generata con successo') 