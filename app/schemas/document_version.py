from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentVersionBase(BaseModel):
    version_number: int = Field(..., description="Version number of the document")
    file_path: str = Field(..., description="Path to the document file")
    file_size: int = Field(..., description="Size of the document file in bytes")
    checksum: str = Field(..., description="Checksum of the document file")
    document_id: int = Field(..., description="ID of the parent document")
    created_by_id: Optional[int] = Field(None, description="ID of the user who created this version")

class DocumentVersionCreate(DocumentVersionBase):
    pass

class DocumentVersionUpdate(BaseModel):
    file_path: Optional[str] = Field(None, description="Updated path to the document file")
    file_size: Optional[int] = Field(None, description="Updated size of the document file in bytes")
    checksum: Optional[str] = Field(None, description="Updated checksum of the document file")

class DocumentVersionInDBBase(DocumentVersionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class DocumentVersion(DocumentVersionInDBBase):
    pass

class DocumentVersionInDB(DocumentVersionInDBBase):
    pass 