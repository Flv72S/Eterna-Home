from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from enum import Enum
from sqlmodel import Field, select, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.node import Node

class MaintenanceStatus(str, Enum):
    """Enum per gli stati di manutenzione."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SCHEDULED = "SCHEDULED"

class MaintenanceRecord(SQLModel, table=True):
    """Modello per la gestione dei record di manutenzione."""
    __tablename__ = "maintenance_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: int = Field(foreign_key="nodes.id")
    description: str
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    performed_by: Optional[str] = None
    tenant_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        index=True,
        description="ID del tenant"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    node: "Node" = Relationship(back_populates="maintenance_records")

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 