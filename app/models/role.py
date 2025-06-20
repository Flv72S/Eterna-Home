"""
Modello Role per la gestione dei ruoli utente
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import ConfigDict
from app.models.user_role import UserRole

if TYPE_CHECKING:
    from app.models.user import User


class RoleBase(SQLModel):
    """Schema base per i ruoli"""
    name: str = Field(unique=True, index=True, description="Nome del ruolo")
    description: Optional[str] = Field(default=None, description="Descrizione del ruolo")
    is_active: bool = Field(default=True, description="Ruolo attivo o disabilitato")


class Role(RoleBase, table=True):
    """Modello Role per il database"""
    __tablename__ = "roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relazione many-to-many con User
    users: List["User"] = Relationship(
        back_populates="roles",
        link_model=UserRole,
        sa_relationship_kwargs={
            "primaryjoin": "Role.id == UserRole.role_id",
            "secondaryjoin": "UserRole.user_id == User.id"
        }
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
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