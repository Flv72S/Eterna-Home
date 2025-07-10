from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, select, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room

class Booking(SQLModel, table=True):
    """Modello per la gestione delle prenotazioni."""
    __tablename__ = "bookings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    house_id: int = Field(foreign_key="houses.id")
    room_id: int = Field(foreign_key="rooms.id")
    start_time: datetime
    end_time: datetime
    status: str = Field(default="pending")
    tenant_id: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    # user: "User" = Relationship(back_populates="bookings")
    room: "Room" = Relationship(back_populates="bookings")

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 