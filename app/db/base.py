from sqlalchemy.orm import declarative_base

# Import all the models, so that Base has them before being
# imported by Alembic
from app.models.user import User  # noqa
from app.models.role import Role  # noqa
from app.models.permission import Permission  # noqa
from app.models.user_role import UserRole  # noqa
from app.models.user_permission import UserPermission  # noqa
from app.models.role_permission import RolePermission  # noqa
from app.models.user_tenant_role import UserTenantRole  # noqa
from app.models.house import House  # noqa
from app.models.room import Room  # noqa
from app.models.booking import Booking  # noqa
from app.models.node import Node  # noqa
from app.models.document import Document  # noqa
from app.models.document_version import DocumentVersion  # noqa
from app.models.maintenance import MaintenanceRecord  # noqa
from app.models.user_house import UserHouse  # noqa
from app.models.bim_model import BIMModel  # noqa
from app.models.audio_log import AudioLog  # noqa
from app.models.ai_interaction import AIAssistantInteraction  # noqa
from app.models.physical_activator import PhysicalActivator  # noqa

# This file is used to import all models and make them available
# to Alembic for database migrations. Do not add any other code here.

Base = declarative_base() 