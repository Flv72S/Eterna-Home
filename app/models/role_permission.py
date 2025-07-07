from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, select, Field

class RolePermission(SQLModel, table=True):
    """Tabella intermedia per relazione many-to-many Role-Permission"""
    __tablename__ = "role_permissions"
    
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow) 