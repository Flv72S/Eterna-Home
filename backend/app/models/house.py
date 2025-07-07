from sqlmodel import SQLModel, select, Field, Relationship
from typing import Optional, List

class House(SQLModel, table=True):
    __tablename__ = "houses"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    owner_id: int = Field(foreign_key="users.id")