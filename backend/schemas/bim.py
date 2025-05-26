from pydantic import BaseModel

class BIMBase(BaseModel):
    # Per ora, non aggiungere campi specifici oltre l'ID.
    # I campi specifici verranno aggiunti quando si definirà la logica dettagliata.
    pass

class BIMCreate(BIMBase):
    pass

class BIM(BIMBase):
    id: int

    class Config:
        from_attributes = True 