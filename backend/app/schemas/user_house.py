from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UserHouseBase(BaseModel):
    user_id: int
    house_id: int

class UserHouseCreate(UserHouseBase):
    pass

class UserHouseUpdate(BaseModel):
    user_id: Optional[int] = None
    house_id: Optional[int] = None

class UserHouse(UserHouseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 