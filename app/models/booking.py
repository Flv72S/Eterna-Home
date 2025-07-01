from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room

class Booking(SQLModel, table=True):
    """Modello per la gestione delle prenotazioni."""
    __tablename__ = "bookings"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    status: str = Field(default="confirmed", description="Stato della prenotazione")
    
    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )
    
    # Relazioni
    user_id: int = Field(foreign_key="users.id")
    room_id: int = Field(foreign_key="rooms.id")
    
    # Date
    start_date: datetime = Field(description="Data di inizio prenotazione")
    end_date: datetime = Field(description="Data di fine prenotazione")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    # user: "User" = Relationship(back_populates="bookings")
    room: "Room" = Relationship(back_populates="bookings")

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 