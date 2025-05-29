from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from backend.models.house import House
    from backend.models.document import Document
    from backend.models.audio_log import AudioLog
    from backend.models.maintenance import Maintenance

class NodeType(str, Enum):
    ROOM = "room"
    AREA = "area"
    DEVICE = "device"

class NodeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Node(SQLModel, table=True):
    __tablename__ = "nodes"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    node_type: str = Field(max_length=50, nullable=False)  # room, area, device, etc.
    house_id: int = Field(foreign_key="houses.id", nullable=False)
    parent_id: Optional[int] = Field(foreign_key="nodes.id", default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    house: "House" = Relationship(back_populates="nodes")
    documents: List["Document"] = Relationship(back_populates="node", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    audio_logs: List["AudioLog"] = Relationship(back_populates="node", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    maintenance_tasks: List["Maintenance"] = Relationship(back_populates="node")
    parent: Optional["Node"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": [id]})
    children: List["Node"] = Relationship(back_populates="parent") 