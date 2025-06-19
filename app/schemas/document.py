from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    """Base schema for Document with common fields"""
    name: str
    type: str
    size: int
    path: str
    checksum: str
    description: Optional[str] = None
    house_id: Optional[int] = None
    node_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Documento Test",
                "type": "application/pdf",
                "size": 1024,
                "path": "/documents/test.pdf",
                "checksum": "abc123",
                "description": "Documento di test",
                "house_id": 1
            }
        }
    )

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    name: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None
    path: Optional[str] = None
    checksum: Optional[str] = None
    description: Optional[str] = None
    house_id: Optional[int] = None
    node_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

class DocumentRead(DocumentBase):
    """Schema for reading a document"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    ) 