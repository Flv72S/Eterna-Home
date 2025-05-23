from pydantic import BaseModel
from datetime import datetime

class AudioLogBase(BaseModel):
    title: str
    file_path: str
    duration: int | None = None

class AudioLogCreate(AudioLogBase):
    node_id: int

class AudioLog(AudioLogBase):
    id: int
    node_id: int
    created_at: datetime

    class Config:
        from_attributes = True 