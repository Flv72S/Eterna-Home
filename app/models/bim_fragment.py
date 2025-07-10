from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime, timezone
import json

if TYPE_CHECKING:
    from .bim_model import BIMModel
    from .node import Node

class BIMFragment(SQLModel, table=True):
    __tablename__ = "bim_fragments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    fragment_type: str = Field(max_length=100)
    geometry_data: Optional[str] = Field(default=None)
    properties: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bim_model_id: Optional[int] = Field(default=None, foreign_key="bim_models.id")
    
    # Attributi aggiuntivi richiesti dai test
    tenant_id: Optional[str] = Field(default=None, max_length=255)
    house_id: Optional[int] = Field(default=None)
    entity_type: Optional[str] = Field(default=None, max_length=100)
    entity_name: Optional[str] = Field(default=None, max_length=255)
    area: Optional[float] = Field(default=None, ge=0)
    volume: Optional[float] = Field(default=None, ge=0)
    level: Optional[int] = Field(default=None)
    ifc_guid: Optional[str] = Field(default=None, max_length=255)
    bounding_box: Optional[str] = Field(default=None)  # JSON string
    bim_metadata: Optional[str] = Field(default=None)  # JSON string
    
    # Relazioni
    bim_model: Optional["BIMModel"] = Relationship(back_populates="fragments")
    nodes: List["Node"] = Relationship(back_populates="bim_fragment")
    
    model_config = {"arbitrary_types_allowed": True}
    
    @property
    def display_name(self) -> str:
        """Restituisce il nome visualizzabile del frammento."""
        if self.entity_name and self.entity_type:
            return f"{self.entity_name} ({self.entity_type})"
        return self.name
    
    @property
    def has_geometry(self) -> bool:
        """Verifica se il frammento ha dati geometrici."""
        return bool(self.geometry_data or self.bounding_box)
    
    @property
    def dimensions(self) -> Optional[Dict[str, float]]:
        """Calcola le dimensioni dal bounding box."""
        if not self.bounding_box:
            return None
        
        try:
            # Gestisce sia stringhe JSON che dizionari Python
            if isinstance(self.bounding_box, str):
                bbox = json.loads(self.bounding_box)
            else:
                bbox = self.bounding_box
            
            return {
                'width': bbox.get('x_max', 0) - bbox.get('x_min', 0),
                'length': bbox.get('y_max', 0) - bbox.get('y_min', 0),
                'height': bbox.get('z_max', 0) - bbox.get('z_min', 0)
            }
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
    
    @property
    def metadata_dict(self) -> Optional[Dict[str, Any]]:
        """Converte bim_metadata da stringa JSON a dizionario."""
        if not self.bim_metadata:
            return None
        
        try:
            if isinstance(self.bim_metadata, str):
                return json.loads(self.bim_metadata)
            return self.bim_metadata
        except json.JSONDecodeError:
            return None
    
    @property
    def bounding_box_dict(self) -> Optional[Dict[str, float]]:
        """Converte bounding_box da stringa JSON a dizionario."""
        if not self.bounding_box:
            return None
        
        try:
            if isinstance(self.bounding_box, str):
                return json.loads(self.bounding_box)
            return self.bounding_box
        except json.JSONDecodeError:
            return None
    
    def is_room(self) -> bool:
        """Verifica se il frammento è una stanza."""
        return self.entity_type == 'room'
    
    def is_hvac(self) -> bool:
        """Verifica se il frammento è un sistema HVAC."""
        return self.entity_type == 'hvac'
    
    def is_plumbing(self) -> bool:
        """Verifica se il frammento è un sistema idraulico."""
        return self.entity_type == 'plumbing'
    
    def is_structure(self) -> bool:
        """Verifica se il frammento è un elemento strutturale."""
        return self.entity_type in ['wall', 'column', 'beam', 'slab']
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Ottiene un valore dai metadati."""
        return self.metadata_dict.get(key, default)
    
    def set_metadata_value(self, key: str, value: Any) -> None:
        """Imposta un valore nei metadati."""
        metadata = self.metadata_dict
        metadata[key] = value
        self.bim_metadata = json.dumps(metadata) 