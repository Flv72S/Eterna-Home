from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class House(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    owner_id: int = Field(foreign_key="user.id")