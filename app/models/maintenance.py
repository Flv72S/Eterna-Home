from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.node import Node

class MaintenanceRecord(SQLModel, table=True):
    """Modello per la gestione dei record di manutenzione."""
    __tablename__ = "maintenance_records"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    maintenance_type: str = Field(description="Tipo di manutenzione")
    priority: str = Field(description="Priorità della manutenzione")
    status: str = Field(default="PENDING", description="Stato della manutenzione")
    
    # Relazioni
    node_id: int = Field(foreign_key="nodes.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    
    # Relazioni
    node: "Node" = Relationship(back_populates="maintenance_records") 