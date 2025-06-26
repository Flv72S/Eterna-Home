from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.role import Role

class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)

class UserPermission(SQLModel, table=True):
    __tablename__ = "user_permissions"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)

class PermissionBase(SQLModel):
    name: str = Field(unique=True, index=True, description="Nome del permesso")
    description: Optional[str] = Field(default=None, description="Descrizione del permesso")
    resource: str = Field(description="Risorsa a cui si applica il permesso")
    action: str = Field(description="Azione consentita (view, edit, delete, manage)")
    is_active: bool = Field(default=True, description="Permesso attivo o disabilitato")

class Permission(PermissionBase, table=True):
    __tablename__ = "permissions"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    roles: List["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermission
    )
    users: List["User"] = Relationship(
        back_populates="permissions",
        link_model=UserPermission
    )
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