from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.main_area import (
    MainAreaCreate, 
    MainAreaUpdate, 
    MainAreaResponse, 
    MainAreaListResponse
)
from app.services.main_area import MainAreaService

router = APIRouter()

@router.post("/", response_model=MainAreaResponse, summary="Crea una nuova area principale")
async def create_main_area(
    main_area_data: MainAreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nuova area principale (MainArea)."""
    try:
        main_area = MainAreaService.create_main_area(db, main_area_data, current_user)
        return main_area
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=MainAreaListResponse, summary="Lista aree principali")
async def get_main_areas(
    house_id: Optional[int] = Query(None, description="Filtra per casa"),
    page: int = Query(1, ge=1, description="Numero di pagina"),
    size: int = Query(100, ge=1, le=1000, description="Dimensione pagina"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene la lista delle aree principali con filtri e paginazione."""
    skip = (page - 1) * size
    result = MainAreaService.get_main_areas(db, current_user, house_id, skip, size)
    return result

@router.get("/{area_id}", response_model=MainAreaResponse, summary="Ottieni area principale")
async def get_main_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene una specifica area principale per ID."""
    main_area = MainAreaService.get_main_area(db, area_id, current_user)
    if not main_area:
        raise HTTPException(status_code=404, detail="Area principale non trovata")
    return main_area

@router.put("/{area_id}", response_model=MainAreaResponse, summary="Aggiorna area principale")
async def update_main_area(
    area_id: int,
    main_area_data: MainAreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un'area principale esistente."""
    try:
        main_area = MainAreaService.update_main_area(db, area_id, main_area_data, current_user)
        if not main_area:
            raise HTTPException(status_code=404, detail="Area principale non trovata")
        return main_area
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{area_id}", summary="Elimina area principale")
async def delete_main_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un'area principale."""
    try:
        success = MainAreaService.delete_main_area(db, area_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Area principale non trovata")
        return {"message": "Area principale eliminata con successo"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/house/{house_id}", response_model=List[MainAreaResponse], summary="Aree principali per casa")
async def get_main_areas_by_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene tutte le aree principali di una casa."""
    areas = MainAreaService.get_areas_by_house(db, house_id, current_user)
    return areas 