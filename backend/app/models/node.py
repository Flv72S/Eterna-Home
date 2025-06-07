from datetime import datetime, UTC
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.maintenance import MaintenanceRecord

class Node(SQLModel, table=True):
    __tablename__ = "nodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str
    location: str
    status: str
    last_maintenance: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)})

    # Relazioni
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="node") 