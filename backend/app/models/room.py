from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Room(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    house_id: int = Field(foreign_key="house.id")