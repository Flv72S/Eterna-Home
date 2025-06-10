from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime

class BookingBase(BaseModel):
    user_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    total_price: float
    status: str

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    total_price: Optional[float] = None
    status: Optional[str] = None

class Booking(BookingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 