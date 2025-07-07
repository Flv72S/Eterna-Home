from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.models.bim_model import BIMFormat, BIMSoftware, BIMLevelOfDetail, BIMConversionStatus

class BIMModelBase(BaseModel):
    """Schema base per BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Nome del modello BIM")
    description: Optional[str] = Field(None, description="Descrizione del modello")
    format: BIMFormat = Field(..., description="Formato del file BIM")
    software_origin: Optional[BIMSoftware] = Field(None, description="Software di origine")
    level_of_detail: Optional[BIMLevelOfDetail] = Field(None, description="Livello di dettaglio")
    revision_date: Optional[datetime] = Field(None, description="Data di revisione")
    file_url: str = Field(..., description="URL del file in storage")
    file_size: int = Field(..., description="Dimensione del file in bytes")
    checksum: str = Field(..., description="Checksum SHA-256 del file")

class BIMModelCreate(BIMModelBase):
    """Schema per la creazione di un BIMModel."""
    user_id: int = Field(..., description="ID dell'utente proprietario")
    house_id: Optional[int] = Field(None, description="ID della casa associata")
    node_id: Optional[int] = Field(None, description="ID del nodo associato")

class BIMModelUpdate(BaseModel):
    """Schema per l'aggiornamento di un BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    description: Optional[str] = None
    software_origin: Optional[BIMSoftware] = None
    level_of_detail: Optional[BIMLevelOfDetail] = None
    revision_date: Optional[datetime] = None
    node_id: Optional[int] = None

class BIMModelResponse(BIMModelBase):
    """Schema per la risposta di un BIMModel."""
    id: int
    user_id: int
    house_id: int
    node_id: Optional[int] = None
    conversion_status: BIMConversionStatus = Field(default=BIMConversionStatus.PENDING)
    conversion_message: Optional[str] = None
    conversion_progress: int = Field(default=0)
    converted_file_url: Optional[str] = None
    validation_report_url: Optional[str] = None
    conversion_started_at: Optional[datetime] = None
    conversion_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Metadati BIM
    total_area: Optional[float] = None
    total_volume: Optional[float] = None
    floor_count: Optional[int] = None
    room_count: Optional[int] = None
    building_height: Optional[float] = None
    project_author: Optional[str] = None
    project_organization: Optional[str] = None
    project_phase: Optional[str] = None
    coordinate_system: Optional[str] = None
    units: Optional[str] = None
    
    # Proprietà calcolate
    has_metadata: bool = Field(description="Indica se il modello ha metadati estratti")
    current_version_number: int = Field(description="Numero di versione corrente")

class BIMModelListResponse(BaseModel):
    """Schema per la risposta della lista di BIMModel."""
    items: List[BIMModelResponse]
    total: int
    page: int
    size: int
    pages: int

# Schemi per versionamento BIM
class BIMModelVersionBase(BaseModel):
    """Schema base per BIMModelVersion."""
    model_config = ConfigDict(from_attributes=True)
    
    version_number: int = Field(..., description="Numero di versione")
    change_description: Optional[str] = Field(None, description="Descrizione delle modifiche")
    change_type: str = Field(default="update", description="Tipo di modifica")
    file_url: str = Field(..., description="URL del file in storage")
    file_size: int = Field(..., description="Dimensione del file in bytes")
    checksum: str = Field(..., description="Checksum SHA-256 del file")

class BIMModelVersionCreate(BIMModelVersionBase):
    """Schema per la creazione di una BIMModelVersion."""
    bim_model_id: int = Field(..., description="ID del modello BIM")
    created_by_id: int = Field(..., description="ID dell'utente che ha creato la versione")

class BIMModelVersionResponse(BIMModelVersionBase):
    """Schema per la risposta di una BIMModelVersion."""
    id: int
    bim_model_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    # Metadati della versione
    total_area: Optional[float] = None
    total_volume: Optional[float] = None
    floor_count: Optional[int] = None
    room_count: Optional[int] = None
    building_height: Optional[float] = None
    
    # Proprietà calcolate
    version_display: str = Field(description="Versione in formato leggibile")
    has_metadata: bool = Field(description="Indica se la versione ha metadati")

class BIMModelVersionListResponse(BaseModel):
    """Schema per la risposta della lista di versioni BIM."""
    items: List[BIMModelVersionResponse]
    total: int
    page: int
    size: int
    pages: int

# Schemi per conversione BIM
class BIMConversionRequest(BaseModel):
    """Schema per richiesta di conversione BIM."""
    model_id: int = Field(..., description="ID del modello da convertire")
    conversion_type: str = Field(default="auto", description="Tipo di conversione (auto, ifc_to_gltf, rvt_to_ifc, validate_only)")
    with_validation: bool = Field(default=True, description="Includere validazione pre/post conversione")

class BIMConversionResponse(BaseModel):
    """Schema per risposta di conversione BIM."""
    success: bool
    model_id: int
    conversion_type: str
    task_id: Optional[str] = None
    message: str
    estimated_duration: Optional[int] = Field(None, description="Durata stimata in secondi")

class BIMConversionStatusResponse(BaseModel):
    """Schema per stato di conversione BIM."""
    model_id: int
    status: BIMConversionStatus
    message: Optional[str] = None
    progress: int = Field(ge=0, le=100)
    converted_file_url: Optional[str] = None
    validation_report_url: Optional[str] = None
    conversion_duration: Optional[float] = None
    updated_at: datetime

class BIMBatchConversionRequest(BaseModel):
    """Schema per richiesta di conversione batch BIM."""
    model_ids: List[int] = Field(..., description="Lista ID modelli da convertire")
    conversion_type: str = Field(default="auto", description="Tipo di conversione")
    max_parallel: int = Field(default=5, description="Numero massimo di conversioni parallele")

class BIMBatchConversionResponse(BaseModel):
    """Schema per risposta di conversione batch BIM."""
    success: bool
    total_models: int
    started_models: int
    failed_models: int
    task_ids: List[str]
    message: str

# Schemi per parsing e metadati BIM
class BIMMetadataResponse(BaseModel):
    """Schema per metadati BIM estratti."""
    model_id: int
    total_area: Optional[float] = None
    total_volume: Optional[float] = None
    floor_count: Optional[int] = None
    room_count: Optional[int] = None
    building_height: Optional[float] = None
    project_author: Optional[str] = None
    project_organization: Optional[str] = None
    project_phase: Optional[str] = None
    coordinate_system: Optional[str] = None
    units: Optional[str] = None
    extracted_at: datetime
    parsing_success: bool
    parsing_message: Optional[str] = None

class BIMUploadResponse(BaseModel):
    """Schema per risposta upload BIM con parsing automatico."""
    model: BIMModelResponse
    metadata: Optional[BIMMetadataResponse] = None
    parsing_status: str = Field(description="Stato del parsing (pending, completed, failed)")
    conversion_triggered: bool = Field(description="Indica se è stata avviata la conversione asincrona") 