from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

class MainAreaBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    floor_level: int = Field(default=0)
    total_area_sqm: Optional[float] = Field(None, ge=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v

class MainAreaCreate(MainAreaBase):
    house_id: int
    tenant_id: str

class MainAreaUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    floor_level: Optional[int] = None
    total_area_sqm: Optional[float] = Field(None, ge=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        return v

class MainArea(MainAreaBase):
    id: int
    house_id: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MainAreaResponse(MainAreaBase):
    id: int
    house_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MainAreaListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: List[MainAreaResponse]
    total: int
    page: int
    size: int
    pages: int 