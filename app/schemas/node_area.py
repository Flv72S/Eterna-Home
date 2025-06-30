from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class NodeAreaBase(BaseModel):
    """Schema base per NodeArea."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100, description="Nome dell'area specifica")
    category: str = Field(..., description="Categoria dell'area")
    has_physical_tag: bool = Field(default=True, description="Se l'area ha un tag fisico NFC")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        allowed_categories = ['residential', 'technical', 'shared']
        if v not in allowed_categories:
            raise ValueError(f'Categoria deve essere una di: {", ".join(allowed_categories)}')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Il nome non può essere vuoto')
        return v.strip()

class NodeAreaCreate(NodeAreaBase):
    """Schema per la creazione di un NodeArea."""
    house_id: int = Field(..., description="ID della casa associata")

class NodeAreaUpdate(BaseModel):
    """Schema per l'aggiornamento di un NodeArea."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    has_physical_tag: Optional[bool] = None
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None:
            allowed_categories = ['residential', 'technical', 'shared']
            if v not in allowed_categories:
                raise ValueError(f'Categoria deve essere una di: {", ".join(allowed_categories)}')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Il nome non può essere vuoto')
        return v.strip() if v else v

class NodeAreaResponse(NodeAreaBase):
    """Schema per la risposta di un NodeArea."""
    id: int
    house_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relazioni
    nodes_count: Optional[int] = Field(None, description="Numero di nodi associati")

class NodeAreaListResponse(BaseModel):
    """Schema per la lista di NodeArea."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[NodeAreaResponse]
    total: int
    page: int
    size: int
    pages: int 