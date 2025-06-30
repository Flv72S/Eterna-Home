from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class AudioLogBase(BaseModel):
    """Schema base per AudioLog."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int = Field(..., description="ID dell'utente che ha inviato il comando")
    node_id: Optional[int] = Field(None, description="ID del nodo associato")
    house_id: Optional[int] = Field(None, description="ID della casa associata")
    transcribed_text: Optional[str] = Field(None, max_length=1000, description="Testo trascritto dal comando vocale")
    response_text: Optional[str] = Field(None, max_length=1000, description="Risposta generata dal sistema")
    processing_status: str = Field(default="received", description="Stato di elaborazione del comando")
    
    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v):
        allowed_statuses = ['received', 'transcribing', 'analyzing', 'completed', 'failed']
        if v not in allowed_statuses:
            raise ValueError(f'Stato deve essere uno di: {", ".join(allowed_statuses)}')
        return v

class AudioLogCreate(AudioLogBase):
    """Schema per la creazione di un AudioLog."""
    pass

class AudioLogUpdate(BaseModel):
    """Schema per l'aggiornamento di un AudioLog."""
    model_config = ConfigDict(from_attributes=True)
    
    transcribed_text: Optional[str] = Field(None, max_length=1000)
    response_text: Optional[str] = Field(None, max_length=1000)
    processing_status: Optional[str] = None
    audio_url: Optional[str] = Field(None, max_length=500)
    
    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v):
        if v is not None:
            allowed_statuses = ['received', 'transcribing', 'analyzing', 'completed', 'failed']
            if v not in allowed_statuses:
                raise ValueError(f'Stato deve essere uno di: {", ".join(allowed_statuses)}')
        return v

class AudioLogResponse(AudioLogBase):
    """Schema per la risposta di un AudioLog."""
    id: int
    timestamp: datetime
    audio_url: Optional[str] = None
    status_display: str
    is_completed: bool
    is_processing: bool

class AudioLogListResponse(BaseModel):
    """Schema per la lista di AudioLog."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[AudioLogResponse]
    total: int
    page: int
    size: int
    pages: int

class VoiceCommandRequest(BaseModel):
    """Schema per la richiesta di comando vocale."""
    model_config = ConfigDict(from_attributes=True)
    
    transcribed_text: Optional[str] = Field(None, max_length=1000, description="Testo trascritto dal comando vocale")
    node_id: Optional[int] = Field(None, description="ID del nodo associato")
    house_id: Optional[int] = Field(None, description="ID della casa associata")
    
    @field_validator('transcribed_text')
    @classmethod
    def validate_transcribed_text(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Il testo trascritto non può essere vuoto')
        return v.strip() if v else v

class VoiceCommandResponse(BaseModel):
    """Schema per la risposta di comando vocale."""
    request_id: str
    status: str
    message: str 