from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MaintenanceTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    node_id: int

class MaintenanceTaskCreate(MaintenanceTaskBase):
    pass

class MaintenanceTaskResponse(MaintenanceTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Alias per compatibilità
MaintenanceTask = MaintenanceTaskResponse 