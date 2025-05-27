from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..models.node import NodeType, NodeStatus

class NodeBase(BaseModel):
    name: str
    type: NodeType
    status: NodeStatus
    house_id: int
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_z: Optional[float] = None

class NodeCreate(NodeBase):
    pass

class Node(NodeBase):
    id: int
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True 