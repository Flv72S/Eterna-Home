from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnnotationBase(BaseModel):
    node_id: int
    user_id: int
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    type: str  # text, image, audio, voice_log

class AnnotationCreate(AnnotationBase):
    pass

class Annotation(AnnotationBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True 