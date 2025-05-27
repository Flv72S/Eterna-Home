from pydantic import BaseModel
from typing import Dict, Optional

class AISampleInput(BaseModel):
    node_id: int
    data: Optional[Dict] = None  # Dati aggiuntivi opzionali per l'analisi 