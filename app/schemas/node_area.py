from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NodeAreaCategory(str, Enum):
    LIVING = "living"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    UTILITY = "utility"
    STORAGE = "storage"
    CORRIDOR = "corridor"
    STAIRS = "stairs"
    OUTDOOR = "outdoor"

class NodeAreaBase(BaseModel):
    name: str = Field(..., max_length=255)
    category: NodeAreaCategory
    description: Optional[str] = Field(None, max_length=1000)
    floor_level: int = Field(default=0)
    area_sqm: Optional[float] = Field(None, ge=0)
    volume_cubic_m: Optional[float] = Field(None, ge=0)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v not in NodeAreaCategory:
            raise ValueError(f'Category must be one of {list(NodeAreaCategory)}')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class NodeAreaCreate(NodeAreaBase):
    house_id: int
    tenant_id: str

class NodeAreaUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[NodeAreaCategory] = None
    description: Optional[str] = Field(None, max_length=1000)
    floor_level: Optional[int] = None
    area_sqm: Optional[float] = Field(None, ge=0)
    volume_cubic_m: Optional[float] = Field(None, ge=0)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in NodeAreaCategory:
            raise ValueError(f'Category must be one of {list(NodeAreaCategory)}')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

class NodeArea(NodeAreaBase):
    id: int
    house_id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

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