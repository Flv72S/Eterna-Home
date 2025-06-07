from app.db.base_class import Base

# Import all models here
from app.models.user import User
from app.models.house import House
from app.models.user_house import UserHouse
from app.models.node import Node
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord

print("Registered tables:", Base.metadata.tables)
print("Registered tables after imports:", Base.metadata.tables) 