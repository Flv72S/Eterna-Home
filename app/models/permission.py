from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped
from pydantic import ConfigDict

from .user_permission import UserPermission
from .role_permission import RolePermission

class PermissionBase(SQLModel):
    name: str = Field(unique=True, index=True, description="Nome del permesso")
    description: Optional[str] = Field(default=None, description="Descrizione del permesso")
    resource: str = Field(description="Risorsa a cui si applica il permesso")
    action: str = Field(description="Azione consentita (view, edit, delete, manage)")
    is_active: bool = Field(default=True, description="Permesso attivo o disabilitato")

class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    
    # Relazioni many-to-many
    users: Mapped[List["User"]] = Relationship(
        back_populates="permissions",
        link_model=UserPermission,
        sa_relationship_kwargs={
            "foreign_keys": [UserPermission.permission_id, UserPermission.user_id]
        }
    )
    roles: Mapped[List["Role"]] = Relationship(
        back_populates="permissions",
        link_model=RolePermission,
        sa_relationship_kwargs={
            "foreign_keys": [RolePermission.permission_id, RolePermission.role_id]
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(SQLModel):
    name: Optional[str] = Field(default=None, description="Nome del permesso")
    description: Optional[str] = Field(default=None, description="Descrizione del permesso")
    resource: Optional[str] = Field(default=None, description="Risorsa a cui si applica il permesso")
    action: Optional[str] = Field(default=None, description="Azione consentita")
    is_active: Optional[bool] = Field(default=None, description="Permesso attivo o disabilitato")

class PermissionRead(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    ) 