from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field(nullable=False)
    content: Optional[str] = None
    node_id: int = Field(foreign_key="nodes.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}) 