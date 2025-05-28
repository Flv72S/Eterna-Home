from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import UploadFile

class LegacyDocumentBase(BaseModel):
    house_id: int
    node_id: int
    type: str
    version: Optional[str] = None

class LegacyDocumentCreate(LegacyDocumentBase):
    file: UploadFile

class LegacyDocument(LegacyDocumentBase):
    id: int
    file_url: str
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True 