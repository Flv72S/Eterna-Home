from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.node import Node
    from app.models.booking import Booking

class Room(SQLModel, table=True):
    """Modello per la rappresentazione di una stanza nel database."""
    __tablename__ = "rooms"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    floor: int
    area: float  # in metri quadrati
    house_id: int = Field(foreign_key="houses.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    house: "House" = Relationship(back_populates="rooms")
    nodes: List["Node"] = Relationship(back_populates="room")
    bookings: List["Booking"] = Relationship(back_populates="room") 