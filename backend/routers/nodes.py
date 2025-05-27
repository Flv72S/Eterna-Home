from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import traceback

from ..db.session import get_db
from ..models.node import Node
from ..models.house import House
from ..schemas.node import NodeCreate, Node as NodeSchema
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.post("/", response_model=NodeSchema)
def create_node(node_data: NodeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Crea un nuovo nodo"""
    try:
        logger.info(f"Tentativo di creazione nodo: {node_data.name}")
        
        # Verifica che la casa esista e appartenga all'utente corrente
        house = db.query(House).filter(
            House.id == node_data.house_id,
            House.owner_id == current_user.id
        ).first()
        
        if not house:
            logger.warning(f"Casa non trovata o non autorizzata: {node_data.house_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="House not found or not authorized"
            )
        
        # Crea il nuovo nodo
        db_node = Node(
            name=node_data.name,
            type=node_data.type,
            status=node_data.status,
            house_id=node_data.house_id,
            location_x=node_data.location_x,
            location_y=node_data.location_y,
            location_z=node_data.location_z
        )
        
        try:
            db.add(db_node)
            db.commit()
            db.refresh(db_node)
            logger.info(f"Nodo creato con successo: {db_node.id}")
            return db_node
        except Exception as db_error:
            logger.error(f"Errore durante la creazione del nodo nel database: {str(db_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating node in database: {str(db_error)}\n{traceback.format_exc()}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore inaspettato durante la creazione del nodo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during node creation: {str(e)}\n{traceback.format_exc()}"
        ) 