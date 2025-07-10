from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .bim_fragment import BIMFragment
    from .room import Room
    from .maintenance import MaintenanceRecord
    from .physical_activator import PhysicalActivator

class NodeCreate(SQLModel):
    """Modello per la creazione di un nodo."""
    name: str = Field(max_length=255)
    node_type: str = Field(max_length=100)
    position_x: float
    position_y: float
    position_z: float
    properties: Optional[str] = Field(default=None)
    bim_fragment_id: Optional[int] = Field(default=None)
    room_id: Optional[int] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None, max_length=255)
    house_id: Optional[int] = Field(default=None)

class Node(SQLModel, table=True):
    __tablename__ = "nodes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    node_type: str = Field(max_length=100)
    position_x: float
    position_y: float
    position_z: float
    properties: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bim_fragment_id: Optional[int] = Field(default=None, foreign_key="bim_fragments.id")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    tenant_id: Optional[str] = Field(default=None, max_length=255)
    house_id: Optional[int] = Field(default=None)
    
    # Relazioni
    bim_fragment: Optional["BIMFragment"] = Relationship(back_populates="nodes")
    room: Optional["Room"] = Relationship(back_populates="nodes")
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="node")
    physical_activators: List["PhysicalActivator"] = Relationship(back_populates="node")
    
    model_config = {"arbitrary_types_allowed": True} 