from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.models.bim_model import BIMFormat, BIMSoftware, BIMLevelOfDetail, BIMConversionStatus

class BIMModelBase(BaseModel):
    """Schema base per BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Nome del modello BIM")
    description: Optional[str] = Field(None, description="Descrizione del modello")
    format: BIMFormat = Field(..., description="Formato del file BIM")
    software_origin: BIMSoftware = Field(..., description="Software di origine")
    level_of_detail: BIMLevelOfDetail = Field(..., description="Livello di dettaglio")
    revision_date: Optional[datetime] = Field(None, description="Data di revisione")
    file_url: str = Field(..., description="URL del file in storage")
    file_size: int = Field(..., description="Dimensione del file in bytes")
    checksum: str = Field(..., description="Checksum SHA-256 del file")

class BIMModelCreate(BIMModelBase):
    """Schema per la creazione di un BIMModel."""
    user_id: int = Field(..., description="ID dell'utente proprietario")
    house_id: int = Field(..., description="ID della casa associata")
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

class BIMModelListResponse(BaseModel):
    """Schema per la lista di BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[BIMModelResponse]
    total: int
    page: int
    size: int
    pages: int

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
    successful: int
    failed: int
    task_ids: List[str]
    message: str 