from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_occupancy: int
    price_per_night: float
    room_type: str

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_occupancy: Optional[int] = None
    price_per_night: Optional[float] = None
    room_type: Optional[str] = None

class Room(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 