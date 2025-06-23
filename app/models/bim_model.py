from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict
from enum import Enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.house import House
    from app.models.node import Node
    from app.models.document_version import DocumentVersion

class BIMFormat(str, Enum):
    """Formati BIM supportati."""
    IFC = "ifc"
    RVT = "rvt"
    DWG = "dwg"
    DXF = "dxf"
    SKP = "skp"
    PLN = "pln"

class BIMSoftware(str, Enum):
    """Software BIM di origine."""
    REVIT = "revit"
    ARCHICAD = "archicad"
    SKETCHUP = "sketchup"
    AUTOCAD = "autocad"
    BLENDER = "blender"
    OTHER = "other"

class BIMLevelOfDetail(str, Enum):
    """Livelli di dettaglio BIM."""
    LOD_100 = "lod_100"
    LOD_200 = "lod_200"
    LOD_300 = "lod_300"
    LOD_400 = "lod_400"
    LOD_500 = "lod_500"

class BIMConversionStatus(str, Enum):
    """Stati di conversione BIM."""
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_FAILED = "validation_failed"
    CLEANED = "cleaned"

class BIMModel(SQLModel, table=True):
    """Modello per la gestione dei modelli BIM."""
    __tablename__ = "bim_models"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    format: BIMFormat = Field(description="Formato del file BIM")
    software_origin: BIMSoftware = Field(description="Software di origine")
    level_of_detail: BIMLevelOfDetail = Field(description="Livello di dettaglio")
    revision_date: Optional[datetime] = Field(default=None, description="Data di revisione")
    
    # File info
    file_url: str = Field(description="URL del file in storage")
    file_size: int = Field(description="Dimensione del file in bytes")
    checksum: str = Field(description="Checksum SHA-256 del file")
    
    # Conversione asincrona
    conversion_status: BIMConversionStatus = Field(default=BIMConversionStatus.PENDING, description="Stato di conversione")
    conversion_message: Optional[str] = Field(default=None, description="Messaggio di stato conversione")
    conversion_progress: int = Field(default=0, description="Progresso conversione (0-100)")
    converted_file_url: Optional[str] = Field(default=None, description="URL del file convertito")
    validation_report_url: Optional[str] = Field(default=None, description="URL del report di validazione")
    conversion_started_at: Optional[datetime] = Field(default=None, description="Data inizio conversione")
    conversion_completed_at: Optional[datetime] = Field(default=None, description="Data completamento conversione")
    
    # Relazioni
    user_id: int = Field(foreign_key="users.id")
    house_id: int = Field(foreign_key="houses.id")
    node_id: Optional[int] = Field(default=None, foreign_key="nodes.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    user: "User" = Relationship(back_populates="bim_models")
    house: "House" = Relationship(back_populates="bim_models")
    node: Optional["Node"] = Relationship(back_populates="bim_models")
    versions: List["DocumentVersion"] = Relationship(
        back_populates="bim_model",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    # Proprietà helper
    @property
    def is_conversion_completed(self) -> bool:
        """Verifica se la conversione è completata."""
        return self.conversion_status == BIMConversionStatus.COMPLETED
    
    @property
    def is_conversion_failed(self) -> bool:
        """Verifica se la conversione è fallita."""
        return self.conversion_status in [BIMConversionStatus.FAILED, BIMConversionStatus.VALIDATION_FAILED]
    
    @property
    def is_conversion_in_progress(self) -> bool:
        """Verifica se la conversione è in corso."""
        return self.conversion_status in [BIMConversionStatus.PROCESSING, BIMConversionStatus.VALIDATING]
    
    @property
    def conversion_duration(self) -> Optional[float]:
        """Calcola la durata della conversione in secondi."""
        if self.conversion_started_at and self.conversion_completed_at:
            return (self.conversion_completed_at - self.conversion_started_at).total_seconds()
        return None 