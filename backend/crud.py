from sqlmodel import Session, select
from typing import List, Optional, Type
from datetime import datetime

# Importa i modelli ORM
from backend.models.house import House

# Importa gli schemi Pydantic
from backend.schemas.house import HouseCreate, HouseUpdate

def create_house(session: Session, house: HouseCreate) -> House:
    """Crea una nuova casa nel database."""
    db_house = House.model_validate(house)
    session.add(db_house)
    session.commit()
    session.refresh(db_house)
    return db_house

def get_house(session: Session, house_id: int) -> Optional[House]:
    """Recupera una singola casa tramite ID."""
    return session.get(House, house_id)

def get_all_houses(session: Session, skip: int = 0, limit: int = 100) -> List[House]:
    """Recupera una lista di case con paginazione."""
    return session.exec(select(House).offset(skip).limit(limit)).all()

def update_house(session: Session, house_id: int, house_update: HouseUpdate) -> Optional[House]:
    """Aggiorna una casa esistente."""
    db_house = session.get(House, house_id)
    if not db_house:
        return None

    # Converti il Pydantic schema in un dizionario, escludendo i campi non settati
    house_data = house_update.model_dump(exclude_unset=True)
    
    # Aggiorna i campi
    for key, value in house_data.items():
        setattr(db_house, key, value)
    
    # Aggiorna il timestamp
    db_house.updated_at = datetime.utcnow()

    session.add(db_house)
    session.commit()
    session.refresh(db_house)
    return db_house

def delete_house(session: Session, house_id: int) -> bool:
    """Cancella una casa tramite ID."""
    db_house = session.get(House, house_id)
    if not db_house:
        return False
    session.delete(db_house)
    session.commit()
    return True

def get_houses_by_owner(session: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[House]:
    """Recupera tutte le case di un proprietario specifico."""
    return session.exec(
        select(House)
        .where(House.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    ).all() 