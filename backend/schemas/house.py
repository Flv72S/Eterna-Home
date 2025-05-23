from pydantic import BaseModel

class HouseBase(BaseModel):
    name: str
    address: str

class HouseCreate(HouseBase):
    pass

class House(HouseBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True 