from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class UserHouse(SQLModel, table=True):
    __tablename__ = "user_houses"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    house_id: int = Field(foreign_key="houses.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}) 