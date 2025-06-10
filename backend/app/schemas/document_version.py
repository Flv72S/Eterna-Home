from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class DocumentVersionBase(BaseModel):
    document_id: int
    version_number: int
    user_id: str
    timestamp: datetime
    storage_path: str
    change_description: Optional[str] = None
    previous_version_id: Optional[int] = None

class DocumentVersionCreate(DocumentVersionBase):
    pass

class DocumentVersionUpdate(BaseModel):
    change_description: Optional[str] = None
    storage_path: Optional[str] = None
    previous_version_id: Optional[int] = None

class DocumentVersion(DocumentVersionBase):
    id: int

    class Config:
        from_attributes = True 