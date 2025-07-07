from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, select, Field

class UserRole(SQLModel, table=True):
    """Tabella intermedia per relazione many-to-many User-Role"""
    __tablename__ = "user_roles"
    
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow) 