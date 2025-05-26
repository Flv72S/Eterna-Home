from pydantic import BaseModel

class VersioningBase(BaseModel):
    # Per ora, non aggiungere campi specifici oltre l'ID.
    # I campi specifici verranno aggiunti quando si definirà la logica dettagliata.
    pass

class VersioningCreate(VersioningBase):
    pass

class Versioning(VersioningBase):
    id: int

    class Config:
        from_attributes = True 