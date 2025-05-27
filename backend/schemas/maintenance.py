from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MaintenanceBase(BaseModel):
    description: Optional[str] = None
    status: str = 'pending'  # pending, in_progress, completed, cancelled
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assigned_to_user_id: Optional[int] = None
    cost: Optional[float] = None
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class Maintenance(MaintenanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 