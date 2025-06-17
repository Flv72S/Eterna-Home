from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="room.id")
    user_id: int = Field(foreign_key="user.id")
    start_date: datetime
    end_date: datetime