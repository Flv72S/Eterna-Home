from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# Schema base per House
class HouseBase(BaseModel):
    name: str
    address: str

# Schema per la creazione di una casa
class HouseCreate(HouseBase):
    pass

# Schema per l'aggiornamento di una casa
class HouseUpdate(HouseBase):
    name: Optional[str] = None
    address: Optional[str] = None

# Schema per la risposta con i dettagli di una casa
class HouseResponse(HouseBase):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

# Schema per la lista di case
class HouseList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    items: List[HouseResponse]
    total: int 