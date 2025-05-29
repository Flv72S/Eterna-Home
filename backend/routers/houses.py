from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional

# Importa le dipendenze
from backend.dependencies import get_db, get_current_user

# Importa gli schemi Pydantic
from backend.schemas.house import HouseCreate, HouseRead, HouseUpdate

# Importa il modulo CRUD
from backend import crud

# Importa il modello User per il tipo hint
from backend.models.user import User as DBUser

# Inizializza il router per le case
router = APIRouter(prefix="/houses", tags=["Houses"])

@router.post("/", response_model=HouseRead, status_code=status.HTTP_201_CREATED)
def create_new_house(
    house: HouseCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Crea una nuova casa assegnandola all'utente autenticato."""
    house.owner_id = current_user.id
    db_house = crud.create_house(db, house=house)
    return db_house

@router.get("/{house_id}", response_model=HouseRead)
def read_house_by_id(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Recupera una singola casa tramite ID."""
    house = crud.get_house(db, house_id=house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house

@router.get("/", response_model=List[HouseRead])
def read_houses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Recupera tutte le case dell'utente autenticato."""
    # Usa get_houses_by_owner invece di get_all_houses per mostrare solo le case dell'utente
    houses = crud.get_houses_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return houses

@router.put("/{house_id}", response_model=HouseRead)
def update_existing_house(
    house_id: int,
    house_update: HouseUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Aggiorna una casa esistente. Solo il proprietario o un admin possono modificarla."""
    db_house = crud.get_house(db, house_id)
    if not db_house:
        raise HTTPException(status_code=404, detail="House not found")

    if db_house.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this house"
        )

    updated_house = crud.update_house(db, house_id=house_id, house_update=house_update)
    if not updated_house:
        raise HTTPException(status_code=404, detail="House not found (failed update)")
    return updated_house

@router.delete("/{house_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Cancella una casa. Solo il proprietario o un admin possono cancellarla."""
    db_house = crud.get_house(db, house_id)
    if not db_house:
        raise HTTPException(status_code=404, detail="House not found")

    if db_house.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this house"
        )

    if not crud.delete_house(db, house_id=house_id):
        raise HTTPException(status_code=404, detail="House not found (failed deletion)")
    return 