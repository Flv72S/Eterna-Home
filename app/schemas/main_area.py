from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class MainAreaBase(BaseModel):
    """Schema base per MainArea."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100, description="Nome dell'area principale")
    description: Optional[str] = Field(None, max_length=500, description="Descrizione dell'area")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Il nome non può essere vuoto')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v

class MainAreaCreate(MainAreaBase):
    """Schema per la creazione di un MainArea."""
    house_id: int = Field(..., description="ID della casa associata")

class MainAreaUpdate(BaseModel):
    """Schema per l'aggiornamento di un MainArea."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Il nome non può essere vuoto')
        return v.strip() if v else v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v

class MainAreaResponse(MainAreaBase):
    """Schema per la risposta di un MainArea."""
    id: int
    house_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relazioni
    nodes_count: Optional[int] = Field(None, description="Numero di nodi associati")

class MainAreaListResponse(BaseModel):
    """Schema per la lista di MainArea."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[MainAreaResponse]
    total: int
    page: int
    size: int
    pages: int 