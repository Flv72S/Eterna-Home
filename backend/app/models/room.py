from datetime import datetime, UTC
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Room(SQLModel, table=True):
    __tablename__ = "rooms"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str
    description: Optional[str] = None
    max_occupancy: int
    price_per_night: float
    room_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}, nullable=False)

    # Relationships
    bookings: List["Booking"] = Relationship(back_populates="room") 