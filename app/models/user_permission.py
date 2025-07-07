from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, select, Field

class UserPermission(SQLModel, table=True):
    """Tabella intermedia per relazione many-to-many User-Permission"""
    __tablename__ = "user_permissions"
    
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow) 