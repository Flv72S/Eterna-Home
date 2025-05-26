from pydantic import BaseModel

class MaintenanceBase(BaseModel):
    # Per ora, non aggiungere campi specifici oltre l'ID.
    # I campi specifici verranno aggiunti quando si definirà la logica dettagliata.
    pass

class MaintenanceCreate(MaintenanceBase):
    pass

class Maintenance(MaintenanceBase):
    id: int

    class Config:
        from_attributes = True 