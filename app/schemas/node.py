from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nfc_id: str
    name: str
    location: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None