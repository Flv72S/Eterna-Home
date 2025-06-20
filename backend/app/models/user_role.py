from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class UserRole(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    assigned_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[int] = Field(foreign_key="users.id") 