from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from app.models import NodeArea, House, Node
from app.schemas.node_area import NodeAreaCreate, NodeAreaUpdate
from app.core.deps import get_current_user
from app.models.user import User

class NodeAreaService:
    """Servizio per la gestione delle NodeArea."""
    
    @staticmethod
    def create_node_area(db: Session, node_area_data: NodeAreaCreate, current_user: User) -> NodeArea:
        """Crea una nuova NodeArea."""
        # Verifica che la casa appartenga all'utente
        house = db.exec(select(House).where(House.id == node_area_data.house_id)).first()
        if not house:
            raise ValueError("Casa non trovata")
        if house.owner_id != current_user.id:
            raise ValueError("Non hai i permessi per creare aree in questa casa")
        
        # Verifica che non esista già un'area con lo stesso nome nella stessa casa
        existing_area = db.exec(
            select(NodeArea).where(
                NodeArea.name == node_area_data.name,
                NodeArea.house_id == node_area_data.house_id
            )
        ).first()
        if existing_area:
            raise ValueError(f"Esiste già un'area con il nome '{node_area_data.name}' in questa casa")
        
        # Crea la nuova area
        node_area = NodeArea(**node_area_data.dict())
        db.add(node_area)
        db.commit()
        db.refresh(node_area)
        return node_area
    
    @staticmethod
    def get_node_area(db: Session, area_id: int, current_user: User) -> Optional[NodeArea]:
        """Ottiene una NodeArea specifica."""
        node_area = db.exec(
            select(NodeArea)
            .join(House)
            .where(
                NodeArea.id == area_id,
                House.owner_id == current_user.id
            )
        ).first()
        return node_area
    
    @staticmethod
    def get_node_areas(
        db: Session, 
        current_user: User,
        house_id: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Ottiene la lista delle NodeArea con filtri e paginazione."""
        query = (
            select(NodeArea)
            .join(House)
            .where(House.owner_id == current_user.id)
        )
        
        # Applica filtri
        if house_id:
            query = query.where(NodeArea.house_id == house_id)
        if category:
            query = query.where(NodeArea.category == category)
        
        # Conta totale
        total_query = (
            select(func.count(NodeArea.id))
            .join(House)
            .where(House.owner_id == current_user.id)
        )
        if house_id:
            total_query = total_query.where(NodeArea.house_id == house_id)
        if category:
            total_query = total_query.where(NodeArea.category == category)
        
        total = db.exec(total_query).first()
        
        # Applica paginazione
        query = query.offset(skip).limit(limit)
        node_areas = db.exec(query).all()
        
        # Aggiungi conteggio nodi per ogni area
        for area in node_areas:
            nodes_count = db.exec(
                select(func.count(Node.id))
                .where(Node.node_area_id == area.id)
            ).first()
            area.nodes_count = nodes_count
        
        return {
            "items": node_areas,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    def update_node_area(
        db: Session, 
        area_id: int, 
        node_area_data: NodeAreaUpdate, 
        current_user: User
    ) -> Optional[NodeArea]:
        """Aggiorna una NodeArea."""
        node_area = NodeAreaService.get_node_area(db, area_id, current_user)
        if not node_area:
            return None
        
        # Verifica che il nuovo nome non sia duplicato (se fornito)
        if node_area_data.name and node_area_data.name != node_area.name:
            existing_area = db.exec(
                select(NodeArea).where(
                    NodeArea.name == node_area_data.name,
                    NodeArea.house_id == node_area.house_id,
                    NodeArea.id != area_id
                )
            ).first()
            if existing_area:
                raise ValueError(f"Esiste già un'area con il nome '{node_area_data.name}' in questa casa")
        
        # Aggiorna i campi
        update_data = node_area_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node_area, field, value)
        
        db.add(node_area)
        db.commit()
        db.refresh(node_area)
        return node_area
    
    @staticmethod
    def delete_node_area(db: Session, area_id: int, current_user: User) -> bool:
        """Elimina una NodeArea."""
        node_area = NodeAreaService.get_node_area(db, area_id, current_user)
        if not node_area:
            return False
        
        # Verifica che non ci siano nodi associati
        nodes_count = db.exec(
            select(func.count(Node.id))
            .where(Node.node_area_id == area_id)
        ).first()
        
        if nodes_count > 0:
            raise ValueError(f"Non è possibile eliminare l'area '{node_area.name}' perché ha {nodes_count} nodi associati")
        
        db.delete(node_area)
        db.commit()
        return True
    
    @staticmethod
    def get_categories() -> List[str]:
        """Restituisce le categorie disponibili."""
        return ['residential', 'technical', 'shared']
    
    @staticmethod
    def get_areas_by_house(db: Session, house_id: int, current_user: User) -> List[NodeArea]:
        """Ottiene tutte le aree di una casa specifica."""
        # Verifica che la casa appartenga all'utente
        house = db.exec(select(House).where(House.id == house_id)).first()
        if not house or house.owner_id != current_user.id:
            return []
        
        return db.exec(
            select(NodeArea)
            .where(NodeArea.house_id == house_id)
            .order_by(NodeArea.name)
        ).all() 