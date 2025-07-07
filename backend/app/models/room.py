from sqlmodel import SQLModel, select, Field, Relationship
from typing import Optional

class Room(SQLModel, table=True):
    __tablename__ = "rooms"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    house_id: int = Field(foreign_key="houses.id")