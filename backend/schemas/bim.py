from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BIMBase(BaseModel):
    house_id: int
    node_id: Optional[int] = None
    bim_file_url: str
    version: str
    format: str  # IFC, RVT, DWG
    size_mb: float
    description: Optional[str] = None

class BIMCreate(BIMBase):
    pass

class BIM(BIMBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True 