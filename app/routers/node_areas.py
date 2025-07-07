from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.node_area import (
    NodeAreaCreate, 
    NodeAreaUpdate, 
    NodeAreaResponse, 
    NodeAreaListResponse
)
from app.services.node_area import NodeAreaService

router = APIRouter()

@router.post("/", response_model=NodeAreaResponse, summary="Crea una nuova area specifica")
async def create_node_area(
    node_area_data: NodeAreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nuova area specifica (NodeArea)."""
    try:
        node_area = NodeAreaService.create_node_area(db, node_area_data, current_user)
        return node_area
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=NodeAreaListResponse, summary="Lista aree specifiche")
async def get_node_areas(
    house_id: Optional[int] = Query(None, description="Filtra per casa"),
    category: Optional[str] = Query(None, description="Filtra per categoria"),
    page: int = Query(1, ge=1, description="Numero di pagina"),
    size: int = Query(100, ge=1, le=1000, description="Dimensione pagina"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene la lista delle aree specifiche con filtri e paginazione."""
    skip = (page - 1) * size
    result = NodeAreaService.get_node_areas(
        db, current_user, house_id, category, skip, size
    )
    return result

@router.get("/{area_id}", response_model=NodeAreaResponse, summary="Ottieni area specifica")
async def get_node_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene una specifica area per ID."""
    node_area = NodeAreaService.get_node_area(db, area_id, current_user)
    if not node_area:
        raise HTTPException(status_code=404, detail="Area non trovata")
    return node_area

@router.put("/{area_id}", response_model=NodeAreaResponse, summary="Aggiorna area specifica")
async def update_node_area(
    area_id: int,
    node_area_data: NodeAreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un'area specifica esistente."""
    try:
        node_area = NodeAreaService.update_node_area(db, area_id, node_area_data, current_user)
        if not node_area:
            raise HTTPException(status_code=404, detail="Area non trovata")
        return node_area
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{area_id}", summary="Elimina area specifica")
async def delete_node_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un'area specifica."""
    try:
        success = NodeAreaService.delete_node_area(db, area_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Area non trovata")
        return {"message": "Area eliminata con successo"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/house/{house_id}", response_model=List[NodeAreaResponse], summary="Aree per casa")
async def get_node_areas_by_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ottiene tutte le aree specifiche di una casa."""
    areas = NodeAreaService.get_areas_by_house(db, house_id, current_user)
    return areas

@router.get("/categories/list", summary="Categorie disponibili")
async def get_categories():
    """Ottiene la lista delle categorie disponibili per le aree."""
    return {"categories": NodeAreaService.get_categories()} 