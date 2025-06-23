from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.node import Node
    from app.models.booking import Booking

class Room(SQLModel, table=True):
    """Modello per la gestione delle stanze."""
    __tablename__ = "rooms"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    room_type: str = Field(description="Tipo di stanza")
    capacity: Optional[int] = Field(default=None, description="Capacità della stanza")
    
    # Relazioni
    house_id: int = Field(foreign_key="houses.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    house: "House" = Relationship(back_populates="rooms")
    nodes: List["Node"] = Relationship(back_populates="room")
    bookings: List["Booking"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    ) 