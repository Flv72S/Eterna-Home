from datetime import datetime, UTC, date
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    room_id: int = Field(foreign_key="rooms.id", nullable=False)
    check_in_date: date
    check_out_date: date
    total_price: float
    status: str  # confirmed, pending, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}, nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="bookings")
    room: "Room" = Relationship(back_populates="bookings") 