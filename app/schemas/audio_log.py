from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AudioLogBase(BaseModel):
    file_path: str = Field(..., max_length=500)
    file_size: int = Field(..., ge=0)
    duration_seconds: Optional[float] = Field(None, ge=0)
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v):
        if v not in ProcessingStatus:
            raise ValueError(f'Processing status must be one of {list(ProcessingStatus)}')
        return v

class AudioLogCreate(AudioLogBase):
    tenant_id: str
    house_id: int
    user_id: Optional[int] = None

class AudioLogUpdate(BaseModel):
    file_path: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = Field(None, ge=0)
    duration_seconds: Optional[float] = Field(None, ge=0)
    processing_status: Optional[ProcessingStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    transcribed_text: Optional[str] = Field(None, max_length=10000)
    processing_result: Optional[Dict[str, Any]] = None

    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v):
        if v is not None and v not in ProcessingStatus:
            raise ValueError(f'Processing status must be one of {list(ProcessingStatus)}')
        return v

    @field_validator('transcribed_text')
    @classmethod
    def validate_transcribed_text(cls, v):
        if v is not None and len(v) > 10000:
            raise ValueError('Transcribed text cannot exceed 10000 characters')
        return v

class AudioLog(AudioLogBase):
    id: int
    tenant_id: str
    house_id: int
    user_id: Optional[int] = None
    transcribed_text: Optional[str] = Field(None, max_length=10000)
    processing_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

class AudioLogResponse(BaseModel):
    id: int
    file_path: str
    file_size: int
    duration_seconds: Optional[float] = None
    processing_status: str
    metadata: Optional[dict] = None
    tenant_id: Optional[str] = None
    house_id: Optional[int] = None
    user_id: Optional[int] = None
    transcribed_text: Optional[str] = None
    processing_result: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 

class AudioLogListResponse(BaseModel):
    items: list[AudioLogResponse]
    total: int
    page: int
    size: int
    pages: int 

class VoiceCommandRequest(BaseModel):
    transcribed_text: str
    node_id: int
    house_id: int 

class VoiceCommandResponse(BaseModel):
    request_id: str
    status: str
    message: str 