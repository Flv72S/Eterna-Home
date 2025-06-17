from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func

from app.models.user import User
from app.models.house import House
from app.schemas.house import HouseCreate, HouseUpdate, HouseResponse, HouseList
from app.db.session import get_session
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/", response_model=HouseResponse, status_code=201)
def create_house(
    house: HouseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> House:
    """Crea una nuova casa per l'utente autenticato."""
    db_house = House(
        name=house.name,
        address=house.address,
        owner_id=current_user.id
    )
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house

@router.get("/", response_model=HouseList)
def list_houses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    fields: Optional[str] = Query(None, description="Campi da includere nella risposta (es. name,address)")
) -> HouseList:
    """Restituisce l'elenco delle case dell'utente autenticato."""
    query = select(House).where(House.owner_id == current_user.id)
    houses = db.exec(query).all()
    
    # Field filtering
    if fields:
        try:
            field_list = [f.strip() for f in fields.split(",")]
            # Verifica che tutti i campi richiesti esistano
            for field in field_list:
                if not hasattr(House, field):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo '{field}' non valido. Campi disponibili: {', '.join(House.__fields__)}"
                    )
            # Filtra i campi nella risposta
            filtered_houses = []
            for house in houses:
                filtered_house = {field: getattr(house, field) for field in field_list}
                filtered_houses.append(filtered_house)
            return HouseList(items=filtered_houses, total=len(filtered_houses))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return HouseList(items=houses, total=len(houses))

@router.get("/{house_id}", response_model=HouseResponse)
def get_house(
    house_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> House:
    """Restituisce i dettagli di una casa, se posseduta dall'utente."""
    house = db.get(House, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    if house.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per accedere a questa casa")
    return house

@router.put("/{house_id}", response_model=HouseResponse)
def update_house(
    house_id: int,
    house_update: HouseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> House:
    """Aggiorna una casa esistente, se posseduta dall'utente."""
    db_house = db.get(House, house_id)
    if not db_house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    if db_house.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per modificare questa casa")
    
    # Aggiorna solo i campi forniti
    house_data = house_update.model_dump(exclude_unset=True)
    for key, value in house_data.items():
        setattr(db_house, key, value)
    
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house

@router.delete("/{house_id}", status_code=204)
def delete_house(
    house_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> None:
    """Elimina una casa esistente, se posseduta dall'utente."""
    db_house = db.get(House, house_id)
    if not db_house:
        raise HTTPException(status_code=404, detail="Casa non trovata")
    if db_house.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per eliminare questa casa")
    
    db.delete(db_house)
    db.commit() 