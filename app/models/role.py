"""
Modello Role per la gestione dei ruoli utente
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING, Any
from sqlmodel import SQLModel, Field, Relationship
from pydantic import ConfigDict
from sqlalchemy.orm import Mapped

from .user_role import UserRole
from .role_permission import RolePermission

if TYPE_CHECKING:
    from .user import User


class RoleBase(SQLModel):
    """Schema base per i ruoli"""
    name: str = Field(unique=True, index=True, description="Nome del ruolo")
    description: Optional[str] = Field(default=None, description="Descrizione del ruolo")
    is_active: bool = Field(default=True, description="Ruolo attivo o disabilitato")


class Role(SQLModel, table=True):
    """Modello Role per il database"""
    __tablename__ = "roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True, description="Ruolo attivo o disabilitato")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    permissions: list["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermission
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        protected_namespaces=()
    )


class RoleCreate(RoleBase):
    """Schema per la creazione di un ruolo"""
    pass


class RoleUpdate(SQLModel):
    """Schema per l'aggiornamento di un ruolo"""
    name: Optional[str] = Field(default=None, description="Nome del ruolo")
    description: Optional[str] = Field(default=None, description="Descrizione del ruolo")
    is_active: Optional[bool] = Field(default=None, description="Ruolo attivo o disabilitato")


class RoleRead(RoleBase):
    """Schema per la lettura di un ruolo"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    ) 