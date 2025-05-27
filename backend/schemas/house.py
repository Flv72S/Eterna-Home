from pydantic import BaseModel
from datetime import datetime

class HouseBase(BaseModel):
    name: str
    address: str

class HouseCreate(HouseBase):
    pass

class House(HouseBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 