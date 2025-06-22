from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nfc_id: str
    name: str
    description: Optional[str] = None
    house_id: int
    room_id: Optional[int] = None 