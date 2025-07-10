from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from app.models import House, Node
# from app.models import MainArea, House, Node
from app.schemas.main_area import MainAreaCreate, MainAreaUpdate
from app.models.user import User

class MainAreaService:
    """Servizio per la gestione delle MainArea (DISABILITATO - MODELLO RIMOSSO)."""
    # Tutte le funzioni relative a MainArea sono state commentate/rimosse per evitare errori.
    pass
    
    # @staticmethod
    # def create_main_area(db: Session, main_area_data: MainAreaCreate, current_user: User) -> MainArea:
    #     """Crea una nuova MainArea."""
    #     pass
    
    # @staticmethod
    # def get_main_area(db: Session, area_id: int, current_user: User) -> Optional[MainArea]:
    #     """Ottiene una MainArea specifica."""
    #     pass
    
    # @staticmethod
    # def get_main_areas(
    #     db: Session, 
    #     current_user: User,
    #     house_id: Optional[int] = None,
    #     skip: int = 0,
    #     limit: int = 100
    # ) -> Dict[str, Any]:
    #     """Ottiene la lista delle MainArea con filtri e paginazione."""
    #     pass
    
    # @staticmethod
    # def update_main_area(
    #     db: Session, 
    #     area_id: int, 
    #     main_area_data: MainAreaUpdate, 
    #     current_user: User
    # ) -> Optional[MainArea]:
    #     """Aggiorna una MainArea."""
    #     pass
    
    # @staticmethod
    # def delete_main_area(db: Session, area_id: int, current_user: User) -> bool:
    #     """Elimina una MainArea."""
    #     pass
    
    # @staticmethod
    # def get_areas_by_house(db: Session, house_id: int, current_user: User) -> List[MainArea]:
    #     """Ottiene tutte le aree principali di una casa specifica."""
    #     pass 