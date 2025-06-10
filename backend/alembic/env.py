import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from alembic import context

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.base import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def create_test_database():
    """Create test database if it doesn't exist."""
    try:
        # Connect to postgres database
        engine = create_engine("postgresql://postgres:N0nn0c4rl0!!@localhost:5432/postgres")
        with engine.connect() as conn:
            # Termina tutte le connessioni al database di test
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'eterna_home_test'
                AND pid <> pg_backend_pid();
            """))
            conn.execute(text("COMMIT"))  # Close any open transaction
            conn.execute(text("DROP DATABASE IF EXISTS eterna_home_test"))
            conn.execute(text("CREATE DATABASE eterna_home_test"))
            logger.info("Test database created successfully")
    except Exception as e:
        logger.error(f"Error creating test database: {str(e)}")
        raise

def get_url():
    # Se siamo in un ambiente di test, usa il database di test
    if os.environ.get("TESTING") == "1":
        create_test_database()
        url = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"
        logger.info("Using test database URL")
    else:
        url = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home"
        logger.info("Using production database URL")
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    try:
        url = get_url()
        logger.info(f"Running offline migrations with URL: {url}")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()
    except Exception as e:
        logger.error(f"Error during offline migration: {str(e)}")
        raise

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    try:
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = get_url()
        logger.info(f"Running online migrations with configuration: {configuration}")
        
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            logger.info("Connected to database successfully")
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                logger.info("Starting migration transaction")
                context.run_migrations()
                logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Error during online migration: {str(e)}")
        raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
