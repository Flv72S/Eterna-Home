from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class NodeBase(BaseModel):
    name: str
    type: str
    location: str
    status: str
    last_maintenance: Optional[datetime] = None

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    last_maintenance: Optional[datetime] = None

class Node(NodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 