from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document
    from app.models.maintenance import MaintenanceRecord
    from app.models.room import Room

class NodeCreate(SQLModel):
    """Modello per la creazione di un nodo."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    name: str
    description: Optional[str] = None
    nfc_id: str = Field(description="Identificativo NFC univoco")
    house_id: int
    room_id: Optional[int] = None

class Node(SQLModel, table=True):
    """Modello per la rappresentazione di un nodo nel database."""
    __tablename__ = "nodes"
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    nfc_id: str = Field(unique=True, index=True, description="Identificativo NFC univoco")
    house_id: int = Field(foreign_key="houses.id")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id", nullable=True)

    # Relazioni
    house: Optional["House"] = Relationship(back_populates="nodes")
    room: Optional["Room"] = Relationship(back_populates="nodes")
    documents: List["Document"] = Relationship(back_populates="node")
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="node") 