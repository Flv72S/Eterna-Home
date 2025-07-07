from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nfc_id: str
    name: str
    description: Optional[str] = None
    house_id: int
    room_id: Optional[int] = None
    node_area_id: Optional[int] = None
    main_area_id: Optional[int] = None
    is_master_node: bool = False
    has_physical_tag: bool = True
    tenant_id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 