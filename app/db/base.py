from sqlalchemy.ext.declarative import declarative_base

# Import all the models, so that Base has them before being
# imported by Alembic
from app.models.user import User  # noqa
from app.models.house import House  # noqa
from app.models.node import Node  # noqa
from app.models.document import Document  # noqa
from app.models.maintenance import MaintenanceRecord  # noqa

# This file is used to import all models and make them available
# to Alembic for database migrations. Do not add any other code here.

Base = declarative_base()

