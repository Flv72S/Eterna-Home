from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from app.models import MainArea, House, Node
from app.schemas.main_area import MainAreaCreate, MainAreaUpdate
from app.models.user import User

class MainAreaService:
    """Servizio per la gestione delle MainArea."""
    
    @staticmethod
    def create_main_area(db: Session, main_area_data: MainAreaCreate, current_user: User) -> MainArea:
        """Crea una nuova MainArea."""
        # Verifica che la casa appartenga all'utente
        house = db.exec(select(House).where(House.id == main_area_data.house_id)).first()
        if not house:
            raise ValueError("Casa non trovata")
        if house.owner_id != current_user.id:
            raise ValueError("Non hai i permessi per creare aree in questa casa")
        
        # Verifica che non esista già un'area con lo stesso nome nella stessa casa
        existing_area = db.exec(
            select(MainArea).where(
                MainArea.name == main_area_data.name,
                MainArea.house_id == main_area_data.house_id
            )
        ).first()
        if existing_area:
            raise ValueError(f"Esiste già un'area principale con il nome '{main_area_data.name}' in questa casa")
        
        # Crea la nuova area
        main_area = MainArea(**main_area_data.dict())
        db.add(main_area)
        db.commit()
        db.refresh(main_area)
        return main_area
    
    @staticmethod
    def get_main_area(db: Session, area_id: int, current_user: User) -> Optional[MainArea]:
        """Ottiene una MainArea specifica."""
        main_area = db.exec(
            select(MainArea)
            .join(House)
            .where(
                MainArea.id == area_id,
                House.owner_id == current_user.id
            )
        ).first()
        return main_area
    
    @staticmethod
    def get_main_areas(
        db: Session, 
        current_user: User,
        house_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Ottiene la lista delle MainArea con filtri e paginazione."""
        query = (
            select(MainArea)
            .join(House)
            .where(House.owner_id == current_user.id)
        )
        
        # Applica filtri
        if house_id:
            query = query.where(MainArea.house_id == house_id)
        
        # Conta totale
        total_query = (
            select(func.count(MainArea.id))
            .join(House)
            .where(House.owner_id == current_user.id)
        )
        if house_id:
            total_query = total_query.where(MainArea.house_id == house_id)
        
        total = db.exec(total_query).first()
        
        # Applica paginazione
        query = query.offset(skip).limit(limit)
        main_areas = db.exec(query).all()
        
        # Aggiungi conteggio nodi per ogni area
        for area in main_areas:
            nodes_count = db.exec(
                select(func.count(Node.id))
                .where(Node.main_area_id == area.id)
            ).first()
            area.nodes_count = nodes_count
        
        return {
            "items": main_areas,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    def update_main_area(
        db: Session, 
        area_id: int, 
        main_area_data: MainAreaUpdate, 
        current_user: User
    ) -> Optional[MainArea]:
        """Aggiorna una MainArea."""
        main_area = MainAreaService.get_main_area(db, area_id, current_user)
        if not main_area:
            return None
        
        # Verifica che il nuovo nome non sia duplicato (se fornito)
        if main_area_data.name and main_area_data.name != main_area.name:
            existing_area = db.exec(
                select(MainArea).where(
                    MainArea.name == main_area_data.name,
                    MainArea.house_id == main_area.house_id,
                    MainArea.id != area_id
                )
            ).first()
            if existing_area:
                raise ValueError(f"Esiste già un'area principale con il nome '{main_area_data.name}' in questa casa")
        
        # Aggiorna i campi
        update_data = main_area_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(main_area, field, value)
        
        db.add(main_area)
        db.commit()
        db.refresh(main_area)
        return main_area
    
    @staticmethod
    def delete_main_area(db: Session, area_id: int, current_user: User) -> bool:
        """Elimina una MainArea."""
        main_area = MainAreaService.get_main_area(db, area_id, current_user)
        if not main_area:
            return False
        
        # Verifica che non ci siano nodi associati
        nodes_count = db.exec(
            select(func.count(Node.id))
            .where(Node.main_area_id == area_id)
        ).first()
        
        if nodes_count > 0:
            raise ValueError(f"Non è possibile eliminare l'area principale '{main_area.name}' perché ha {nodes_count} nodi associati")
        
        db.delete(main_area)
        db.commit()
        return True
    
    @staticmethod
    def get_areas_by_house(db: Session, house_id: int, current_user: User) -> List[MainArea]:
        """Ottiene tutte le aree principali di una casa specifica."""
        # Verifica che la casa appartenga all'utente
        house = db.exec(select(House).where(House.id == house_id)).first()
        if not house or house.owner_id != current_user.id:
            return []
        
        return db.exec(
            select(MainArea)
            .where(MainArea.house_id == house_id)
            .order_by(MainArea.name)
        ).all() 