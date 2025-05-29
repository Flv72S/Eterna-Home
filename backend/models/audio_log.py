from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.node import Node

class AudioLog(SQLModel, table=True):
    __tablename__ = "audio_logs"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    file_path: str = Field(max_length=255, nullable=False)
    duration: Optional[float] = Field(default=None)
    node_id: int = Field(foreign_key="nodes.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    node: "Node" = Relationship(back_populates="audio_logs") 