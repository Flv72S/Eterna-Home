from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class HouseBase(BaseModel):
    name: str
    address: str

class HouseCreate(HouseBase):
    pass

class HouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

class House(HouseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 