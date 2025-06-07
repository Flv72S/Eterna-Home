from datetime import datetime, UTC
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.node import Node

class MaintenanceStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MaintenanceRecord(SQLModel, table=True):
    __tablename__ = "maintenance_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: int = Field(foreign_key="nodes.id")
    date: datetime
    type: str
    description: str
    status: MaintenanceStatus
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)})

    # Relazione con Node
    node: "Node" = Relationship(back_populates="maintenance_records") 