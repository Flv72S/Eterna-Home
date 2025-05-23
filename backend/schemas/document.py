from pydantic import BaseModel
from datetime import datetime

class DocumentBase(BaseModel):
    title: str
    content: str | None = None
    file_path: str | None = None

class DocumentCreate(DocumentBase):
    node_id: int

class Document(DocumentBase):
    id: int
    node_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 