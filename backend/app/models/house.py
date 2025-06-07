from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel

class House(SQLModel, table=True):
    __tablename__ = "houses"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(nullable=False)
    address: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}) 