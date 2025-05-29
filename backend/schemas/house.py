from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base per la creazione e l'aggiornamento
class HouseBase(BaseModel):
    name: str
    address: str  # Non più opzionale, come nel modello
    description: Optional[str] = None  # Manteniamo questo campo per estensibilità futura

# Schema per la creazione di una nuova casa
class HouseCreate(HouseBase):
    owner_id: int

# Schema per l'aggiornamento di una casa esistente (tutti i campi sono opzionali)
class HouseUpdate(HouseBase):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None

# Schema per la lettura/risposta di una casa (include ID e campi generati dal DB)
class HouseRead(HouseBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime  # Non più opzionale, come nel modello

    class Config:
        from_attributes = True 