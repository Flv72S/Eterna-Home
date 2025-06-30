from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class UserPermission(SQLModel, table=True):
    """Tabella intermedia per relazione many-to-many User-Permission"""
    __tablename__ = "user_permissions"
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", primary_key=True)
    permission_id: Optional[int] = Field(default=None, foreign_key="permissions.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[int] = Field(default=None, foreign_key="users.id", description="ID dell'utente che ha assegnato il permesso") 