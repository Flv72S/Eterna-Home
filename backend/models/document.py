from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.node import Node

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    file_path: str = Field(max_length=255, nullable=False)
    file_type: str = Field(max_length=50, nullable=False)
    node_id: int = Field(foreign_key="nodes.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    node: "Node" = Relationship(back_populates="documents") 