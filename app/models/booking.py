from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.room import Room

class Booking(SQLModel, table=True):
    """Modello per la rappresentazione di una prenotazione nel database."""
    __tablename__ = "bookings"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="rooms.id")
    user_id: int = Field(foreign_key="users.id")
    start_time: datetime
    end_time: datetime
    status: str = Field(default="pending")  # pending, confirmed, cancelled
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    room: "Room" = Relationship(back_populates="bookings")
    user: "User" = Relationship(back_populates="bookings") 