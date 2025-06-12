from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

from app.models.node import Node
from app.models.document import Document

class MaintenanceStatus(str, Enum):
    """Enum per lo stato della manutenzione"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class MaintenanceType(str, Enum):
    """Enum per il tipo di manutenzione"""
    ROUTINE = "routine"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"

class MaintenanceRecord(SQLModel, table=True):
    """Modello per i record di manutenzione dei nodi"""
    
    __tablename__ = "maintenance_records"

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "node_id": 1,
                "timestamp": "2024-03-15T10:30:00",
                "maintenance_type": "routine",
                "description": "Manutenzione programmata del sensore",
                "status": "pending",
                "notes": "Da verificare il funzionamento del sensore di temperatura",
                "document_id": 1
            }
        }
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: int = Field(foreign_key="nodes.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    maintenance_type: MaintenanceType
    description: str
    status: MaintenanceStatus = Field(default=MaintenanceStatus.PENDING)
    notes: Optional[str] = None
    document_id: Optional[int] = Field(default=None, foreign_key="documents.id")

    # Relazioni
    node: Node = Relationship(back_populates="maintenance_records")
    document: Optional[Document] = Relationship(back_populates="maintenance_records") 