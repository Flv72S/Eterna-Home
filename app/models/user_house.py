from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, select, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.house import House

class UserHouse(SQLModel, table=True):
    """
    Modello per la relazione many-to-many tra utenti e case.
    Permette a un utente di essere associato a più case all'interno del proprio tenant.
    """
    
    __tablename__ = "user_houses"
    
    # Chiavi primarie composite
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    house_id: int = Field(foreign_key="houses.id", primary_key=True)
    
    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )
    
    # Ruolo dell'utente nella casa specifica
    role_in_house: Optional[str] = Field(
        default=None, 
        max_length=50,
        description="Ruolo dell'utente nella casa specifica (es: owner, resident, guest, manager)"
    )
    
    # Permessi specifici per casa
    permissions: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Permessi specifici per casa (JSON string)"
    )
    
    # Stato dell'associazione
    is_active: bool = Field(
        default=True,
        description="Indica se l'associazione utente-casa è attiva"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni (temporaneamente commentate per compatibilità SQLAlchemy 2.0+)
    # user: "User" = Relationship(back_populates="user_houses")
    # house: "House" = Relationship(back_populates="user_houses")
    
    def __repr__(self) -> str:
        return f"<UserHouse user_id={self.user_id} house_id={self.house_id} tenant_id={self.tenant_id}>" 