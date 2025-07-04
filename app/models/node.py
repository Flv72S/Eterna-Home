from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document
    from app.models.maintenance import MaintenanceRecord
    from app.models.room import Room
    from app.models.bim_model import BIMModel
    from app.models.audio_log import AudioLog
    from app.models.physical_activator import PhysicalActivator

class NodeArea(SQLModel, table=True):
    """Modello per le aree specifiche associate ai nodi."""
    __tablename__ = "node_areas"
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Cucina", "Bagno", "Quadro Elettrico"
    category: str = Field(index=True)  # es. "residential", "technical", "shared"
    has_physical_tag: bool = True  # se ha attivatore fisico o meno
    house_id: int = Field(foreign_key="houses.id")  # per multi-tenancy

    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )

    # Relazioni
    # house: Optional["House"] = Relationship(back_populates="node_areas")
    nodes: List["Node"] = Relationship(back_populates="node_area")

class MainArea(SQLModel, table=True):
    """Modello per le aree principali che raggruppano nodi."""
    __tablename__ = "main_areas"
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # es. "Zona Giorno", "Zona Impianti"
    description: Optional[str] = None
    house_id: int = Field(foreign_key="houses.id")  # per multi-tenancy

    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )

    # Relazioni
    # house: Optional["House"] = Relationship(back_populates="main_areas")
    nodes: List["Node"] = Relationship(back_populates="main_area")

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
    node_area_id: Optional[int] = None
    main_area_id: Optional[int] = None
    is_master_node: bool = False
    has_physical_tag: bool = True

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
    node_area_id: Optional[int] = Field(default=None, foreign_key="node_areas.id", nullable=True)
    main_area_id: Optional[int] = Field(default=None, foreign_key="main_areas.id", nullable=True)
    is_master_node: bool = False  # se rappresenta l'area principale
    has_physical_tag: bool = True

    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )

    # Relazioni
    # house: Optional["House"] = Relationship(back_populates="nodes")
    room: Optional["Room"] = Relationship(back_populates="nodes")
    node_area: Optional["NodeArea"] = Relationship(back_populates="nodes")
    main_area: Optional["MainArea"] = Relationship(back_populates="nodes")
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="node")
    # bim_models: List["BIMModel"] = Relationship(
    #     back_populates="node",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    # )
    # audio_logs: List["AudioLog"] = Relationship(back_populates="node")
    physical_activators: List["PhysicalActivator"] = Relationship(back_populates="linked_node")

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 