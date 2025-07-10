from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class BIMModelBase(BaseModel):
    """Schema base per BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Nome del modello BIM")
    description: Optional[str] = Field(None, description="Descrizione del modello")
    file_path: str = Field(..., description="Percorso del file")
    file_size: int = Field(..., description="Dimensione del file in bytes")

class BIMModelCreate(BIMModelBase):
    """Schema per la creazione di un BIMModel."""
    house_id: Optional[int] = Field(None, description="ID della casa associata")

class BIMModelUpdate(BaseModel):
    """Schema per l'aggiornamento di un BIMModel."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    description: Optional[str] = None

class BIMModelResponse(BIMModelBase):
    """Schema per la risposta di un BIMModel."""
    id: int
    upload_date: datetime
    last_modified: datetime
    status: str
    conversion_progress: int
    house_id: Optional[int] = None

class BIMModelListResponse(BaseModel):
    """Schema per la risposta della lista di BIMModel."""
    items: List[BIMModelResponse]
    total: int
    page: int
    size: int
    pages: int

# Schemi per conversione BIM
class BIMConversionRequest(BaseModel):
    """Schema per richiesta di conversione BIM."""
    model_id: int = Field(..., description="ID del modello da convertire")

class BIMConversionResponse(BaseModel):
    """Schema per risposta di conversione BIM."""
    success: bool
    model_id: int
    message: str

class BIMConversionStatusResponse(BaseModel):
    """Schema per stato di conversione BIM."""
    model_id: int
    status: str
    message: Optional[str] = None
    progress: int = Field(ge=0, le=100)

class BIMBatchConversionRequest(BaseModel):
    """Schema per richiesta di conversione batch BIM."""
    model_ids: List[int] = Field(..., description="Lista ID modelli da convertire")

class BIMBatchConversionResponse(BaseModel):
    """Schema per risposta di conversione batch BIM."""
    success: bool
    total_models: int
    started_models: int
    failed_models: int
    message: str

# Schemi per parsing e metadati BIM
class BIMMetadataResponse(BaseModel):
    """Schema per metadati BIM estratti."""
    model_id: int
    extracted_at: datetime
    parsing_success: bool
    parsing_message: Optional[str] = None

class BIMUploadResponse(BaseModel):
    """Schema per risposta upload BIM con parsing automatico."""
    model: BIMModelResponse
    metadata: Optional[BIMMetadataResponse] = None
    parsing_status: str = Field(description="Stato del parsing (pending, completed, failed)")
    conversion_triggered: bool = Field(description="Indica se è stata avviata la conversione asincrona")

# Schemi per versionamento (temporaneamente semplificati)
class BIMModelVersionResponse(BaseModel):
    """Schema per la risposta di una BIMModelVersion."""
    id: int
    version_number: int
    created_at: datetime

class BIMModelVersionListResponse(BaseModel):
    """Schema per la risposta della lista di versioni BIM."""
    items: List[BIMModelVersionResponse]
    total: int
    page: int
    size: int
    pages: int 