from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class DocumentBase(BaseModel):
    """Base schema for Document with common fields"""
    title: str = Field(description="Nome del documento")
    document_type: Optional[str] = Field(default="general", description="Tipo di documento (general, contract, manual, etc.)")
    file_type: str = Field(description="Tipo MIME del file")
    file_size: int = Field(description="Dimensione del file in bytes")
    file_url: str = Field(description="URL del file in storage")
    checksum: str
    description: Optional[str] = None
    house_id: Optional[int] = None
    node_id: Optional[int] = None
    
    # Campi specifici per manuali PDF
    device_name: Optional[str] = Field(default=None, description="Nome dell'oggetto/elettrodomestico")
    brand: Optional[str] = Field(default=None, description="Marca dell'oggetto")
    model: Optional[str] = Field(default=None, description="Modello dell'oggetto")
    external_link: Optional[str] = Field(default=None, description="Link esterno al manuale")
    room_id: Optional[int] = Field(default=None, description="ID della stanza associata")

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "title": "Documento Test",
                "file_type": "application/pdf",
                "file_size": 1024,
                "file_url": "/documents/test.pdf",
                "checksum": "abc123",
                "description": "Documento di test",
                "house_id": 1,
                "device_name": "Lavatrice",
                "brand": "Samsung",
                "model": "WW90T554DAW"
            }
        }
    )

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    document_type: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    checksum: Optional[str] = None
    description: Optional[str] = None
    house_id: Optional[int] = None
    node_id: Optional[int] = None
    
    # Campi specifici per manuali PDF
    device_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    external_link: Optional[str] = None
    room_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        populate_by_name=True
    )

class DocumentRead(DocumentBase):
    """Schema for reading a document"""
    id: int
    owner_id: int
    tenant_id: str
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        populate_by_name=True
    ) 