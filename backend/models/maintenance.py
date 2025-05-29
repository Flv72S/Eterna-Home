from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.house import House
    from backend.models.node import Node

class Maintenance(SQLModel, table=True):
    __tablename__ = "maintenance"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    status: str = Field(max_length=50, nullable=False)  # pending, in_progress, completed, cancelled
    priority: str = Field(max_length=50, nullable=False)  # low, medium, high, critical
    house_id: int = Field(foreign_key="houses.id", nullable=False)
    node_id: Optional[int] = Field(foreign_key="nodes.id", default=None)
    assigned_to_id: Optional[int] = Field(foreign_key="users.id", default=None)
    scheduled_date: Optional[datetime] = Field(default=None)
    completed_date: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    house: "House" = Relationship(back_populates="maintenance_tasks")
    node: Optional["Node"] = Relationship(back_populates="maintenance_tasks")
    assigned_to: Optional["User"] = Relationship(back_populates="maintenance_tasks")

class MaintenanceTask(SQLModel, table=True):
    __tablename__ = "maintenance_tasks"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=100, nullable=False)
    description: str = Field(max_length=255, nullable=False)
    status: str = Field(max_length=20, default="pending")
    priority: str = Field(max_length=20, default="medium")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    node_id: Optional[int] = Field(foreign_key="nodes.id", nullable=False)

    # Relationships
    node: Optional["Node"] = Relationship(back_populates="maintenance_tasks") 