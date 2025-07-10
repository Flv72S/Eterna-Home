from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from pydantic import BaseModel, ConfigDict, Field

class BIMFragmentBase(BaseModel):
    """Schema base per BIMFragment."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,
        extra='allow'
    )

    entity_type: str = Field(
        description="Tipo di entità BIM (room, HVAC, plumbing, structure, furniture, etc.)"
    )
    entity_name: str = Field(
        description="Nome dell'entità BIM"
    )
    area: Optional[float] = Field(
        default=None,
        description="Area dell'entità in metri quadrati"
    )
    volume: Optional[float] = Field(
        default=None,
        description="Volume dell'entità in metri cubi"
    )
    level: Optional[int] = Field(
        default=None,
        description="Livello/piano dell'entità"
    )
    ifc_guid: Optional[str] = Field(
        default=None,
        description="GUID IFC dell'entità originale"
    )
    bounding_box: Optional[Dict[str, float]] = Field(
        default=None,
        description="Bounding box dell'entità {x_min, y_min, z_min, x_max, y_max, z_max}"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadati aggiuntivi dell'entità BIM"
    )

class BIMFragmentCreate(BIMFragmentBase):
    """Schema per la creazione di un BIMFragment."""
    tenant_id: uuid.UUID = Field(
        description="ID del tenant per isolamento multi-tenant"
    )
    house_id: int = Field(
        description="ID della casa associata al frammento"
    )
    bim_model_id: int = Field(
        description="ID del modello BIM di origine"
    )
    node_id: Optional[int] = Field(
        default=None,
        description="ID del nodo Eterna associato"
    )

class BIMFragmentUpdate(BaseModel):
    """Schema per l'aggiornamento di un BIMFragment."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,
        extra='allow'
    )

    entity_type: Optional[str] = Field(
        default=None,
        description="Tipo di entità BIM"
    )
    entity_name: Optional[str] = Field(
        default=None,
        description="Nome dell'entità BIM"
    )
    area: Optional[float] = Field(
        default=None,
        description="Area dell'entità in metri quadrati"
    )
    volume: Optional[float] = Field(
        default=None,
        description="Volume dell'entità in metri cubi"
    )
    level: Optional[int] = Field(
        default=None,
        description="Livello/piano dell'entità"
    )
    ifc_guid: Optional[str] = Field(
        default=None,
        description="GUID IFC dell'entità originale"
    )
    bounding_box: Optional[Dict[str, float]] = Field(
        default=None,
        description="Bounding box dell'entità"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadati aggiuntivi dell'entità BIM"
    )
    node_id: Optional[int] = Field(
        default=None,
        description="ID del nodo Eterna associato"
    )

class BIMFragmentRead(BIMFragmentBase):
    """Schema per la lettura di un BIMFragment."""
    id: int = Field(description="ID del frammento")
    tenant_id: uuid.UUID = Field(description="ID del tenant")
    house_id: int = Field(description="ID della casa")
    bim_model_id: int = Field(description="ID del modello BIM")
    node_id: Optional[int] = Field(description="ID del nodo Eterna associato")
    created_at: datetime = Field(description="Data di creazione")
    updated_at: datetime = Field(description="Data di ultimo aggiornamento")

    # Campi calcolati per il frontend
    display_name: str = Field(description="Nome di visualizzazione")
    has_geometry: bool = Field(description="Indica se ha informazioni geometriche")
    dimensions: Optional[Dict[str, float]] = Field(
        default=None,
        description="Dimensioni calcolate dal bounding box"
    )

class BIMFragmentList(BaseModel):
    """Schema per la lista di BIMFragment."""
    fragments: List[BIMFragmentRead] = Field(description="Lista dei frammenti")
    total: int = Field(description="Numero totale di frammenti")
    page: int = Field(description="Pagina corrente")
    size: int = Field(description="Dimensione della pagina")

class BIMFragmentStats(BaseModel):
    """Schema per le statistiche dei frammenti BIM."""
    total_fragments: int = Field(description="Numero totale di frammenti")
    fragments_by_type: Dict[str, int] = Field(description="Frammenti raggruppati per tipo")
    total_area: float = Field(description="Area totale dei frammenti")
    total_volume: float = Field(description="Volume totale dei frammenti")
    levels: List[int] = Field(description="Livelli presenti")

class BIMUploadResponse(BaseModel):
    """Schema per la risposta dell'upload BIM."""
    bim_model_id: int = Field(description="ID del modello BIM creato")
    fragments_count: int = Field(description="Numero di frammenti estratti")
    nodes_created: int = Field(description="Numero di nodi Eterna creati")
    processing_time: float = Field(description="Tempo di elaborazione in secondi")
    message: str = Field(description="Messaggio di conferma")

class BIMFragmentFilter(BaseModel):
    """Schema per il filtro dei frammenti BIM."""
    entity_type: Optional[str] = Field(
        default=None,
        description="Filtra per tipo di entità"
    )
    level: Optional[int] = Field(
        default=None,
        description="Filtra per livello"
    )
    min_area: Optional[float] = Field(
        default=None,
        description="Area minima"
    )
    max_area: Optional[float] = Field(
        default=None,
        description="Area massima"
    )
    has_node: Optional[bool] = Field(
        default=None,
        description="Filtra per presenza di nodo associato"
    )
    search: Optional[str] = Field(
        default=None,
        description="Ricerca nel nome dell'entità"
    ) 