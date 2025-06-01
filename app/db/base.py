from sqlalchemy.ext.declarative import declarative_base

# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.session import Base  # noqa
from app.models.user import User  # noqa

# This file is used to import all models and make them available
# to Alembic for database migrations. Do not add any other code here.

Base = declarative_base()

