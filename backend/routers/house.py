from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
import traceback

from backend.db.session import get_db
from backend.models.house import House
from backend.models.user import User
from backend.schemas.house import HouseCreate, House as HouseSchema
from backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/houses", tags=["houses"])

@router.post("/", response_model=HouseSchema)
def create_house(house: HouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Crea una nuova casa"""
    try:
        logger.info(f"Tentativo di creazione casa: {house.name}")
        
        # Crea la nuova casa
        db_house = House(
            name=house.name,
            address=house.address,
            owner_id=current_user.id
        )
        
        try:
            db.add(db_house)
            db.commit()
            db.refresh(db_house)
            logger.info(f"Casa creata con successo: {db_house.id}")
            return db_house
        except Exception as db_error:
            logger.error(f"Errore durante la creazione della casa nel database: {str(db_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating house in database: {str(db_error)}\n{traceback.format_exc()}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore inaspettato durante la creazione della casa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during house creation: {str(e)}\n{traceback.format_exc()}"
        )

@router.get("/", response_model=List[HouseSchema])
def read_houses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ottiene la lista delle case dell'utente"""
    try:
        houses = db.query(House).filter(House.owner_id == current_user.id).offset(skip).limit(limit).all()
        return houses
    except Exception as e:
        logger.error(f"Errore durante il recupero delle case: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving houses: {str(e)}"
        )

@router.get("/{house_id}", response_model=HouseSchema)
def read_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ottiene una casa specifica"""
    try:
        house = db.query(House).filter(House.id == house_id, House.owner_id == current_user.id).first()
        if house is None:
            raise HTTPException(status_code=404, detail="House not found")
        return house
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero della casa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving house: {str(e)}"
        )

@router.delete("/{house_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Elimina una casa"""
    try:
        house = db.query(House).filter(House.id == house_id, House.owner_id == current_user.id).first()
        if house is None:
            raise HTTPException(status_code=404, detail="House not found")
        db.delete(house)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante l'eliminazione della casa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while deleting house: {str(e)}"
        ) 