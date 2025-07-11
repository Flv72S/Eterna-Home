from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict

class UserHouseBase(BaseModel):
    """Schema base per UserHouse."""
    role_in_house: Optional[str] = Field(
        default=None, 
        max_length=50,
        description="Ruolo dell'utente nella casa specifica"
    )
    permissions: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Permessi specifici per casa (JSON string)"
    )
    is_active: bool = Field(
        default=True,
        description="Indica se l'associazione utente-casa è attiva"
    )

class UserHouseCreate(UserHouseBase):
    """Schema per la creazione di una associazione UserHouse."""
    user_id: int = Field(description="ID dell'utente")
    house_id: int = Field(description="ID della casa")
    tenant_id: str = Field(description="ID del tenant")

class UserHouseUpdate(BaseModel):
    """Schema per l'aggiornamento di una associazione UserHouse."""
    role_in_house: Optional[str] = Field(
        default=None, 
        max_length=50,
        description="Ruolo dell'utente nella casa specifica"
    )
    permissions: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Permessi specifici per casa (JSON string)"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Indica se l'associazione utente-casa è attiva"
    )

class UserHouseResponse(UserHouseBase):
    """Schema per la risposta di una associazione UserHouse."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    house_id: int
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class UserHouseList(BaseModel):
    """Schema per la lista di associazioni UserHouse."""
    items: list[UserHouseResponse]
    total: int
    page: int
    size: int
    pages: int

class HouseAccessRequest(BaseModel):
    """Schema per richiedere accesso a una casa."""
    house_id: int = Field(description="ID della casa")
    role_in_house: Optional[str] = Field(
        default="resident",
        max_length=50,
        description="Ruolo richiesto nella casa"
    )
    permissions: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Permessi specifici richiesti"
    )

class HouseAccessResponse(BaseModel):
    """Schema per la risposta di accesso a una casa."""
    success: bool
    message: str
    user_house: Optional[UserHouseResponse] = None

class UserHouseSummary(BaseModel):
    """Schema per il riepilogo delle case di un utente."""
    model_config = ConfigDict(from_attributes=True)
    
    house_id: int
    house_name: str
    house_address: str
    role_in_house: Optional[str]
    is_owner: bool
    is_active: bool
    created_at: datetime 