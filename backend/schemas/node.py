from pydantic import BaseModel
from datetime import datetime

class NodeBase(BaseModel):
    name: str
    type: str
    status: str = "active"

class NodeCreate(NodeBase):
    house_id: int

class Node(NodeBase):
    id: int
    house_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 