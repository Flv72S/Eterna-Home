from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.node import Node

class Annotation(SQLModel, table=True):
    __tablename__ = "annotations"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(max_length=1000, nullable=False)
    node_id: int = Field(foreign_key="nodes.id", nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    node: "Node" = Relationship(back_populates="annotations")
    user: "User" = Relationship(back_populates="annotations") 