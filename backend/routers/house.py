from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import get_db
from backend.models.house import House
from backend.models.user import User
from backend.schemas.house import HouseCreate, House as HouseSchema
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/houses", tags=["houses"])

@router.post("/", response_model=HouseSchema)
def create_house(house: HouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_house = House(**house.dict(), owner_id=current_user.id)
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house

@router.get("/", response_model=List[HouseSchema])
def read_houses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    houses = db.query(House).filter(House.owner_id == current_user.id).offset(skip).limit(limit).all()
    return houses

@router.get("/{house_id}", response_model=HouseSchema)
def read_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    house = db.query(House).filter(House.id == house_id, House.owner_id == current_user.id).first()
    if house is None:
        raise HTTPException(status_code=404, detail="House not found")
    return house

@router.delete("/{house_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    house = db.query(House).filter(House.id == house_id, House.owner_id == current_user.id).first()
    if house is None:
        raise HTTPException(status_code=404, detail="House not found")
    db.delete(house)
    db.commit()
    return None 