from pydantic import BaseModel
from typing import Dict, Any

class AISampleInput(BaseModel):
    node_id: int
    data: Dict[str, Any] 