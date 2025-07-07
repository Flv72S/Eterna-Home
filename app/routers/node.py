from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.models.node import Node, NodeCreate
from app.models.user import User
from app.database import get_session
from app.utils.security import get_current_user
from app.db.utils import safe_exec
from app.schemas.node import NodeResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/nodes")
logger = get_logger(__name__)

@router.get("/", response_model=List[NodeResponse])
async def read_nodes(
    skip: int = 0,
    limit: int = 100,
    house_id: Optional[int] = Query(None, description="Filtra per casa"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Ottiene la lista dei nodi."""
    logger.info("Nodes list request",
                user_id=current_user.id,
                skip=skip,
                limit=limit,
                house_id=house_id)
    
    query = select(Node)
    if house_id:
        query = query.where(Node.house_id == house_id)
    query = query.offset(skip).limit(limit)
    result = safe_exec(session, query)
    nodes = result.all()
    
    logger.info("Nodes list retrieved",
                user_id=current_user.id,
                count=len(nodes),
                house_id=house_id)
    
    return nodes

@router.post("/", response_model=NodeResponse)
async def create_node(
    node: NodeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuovo nodo."""
    logger.info("Node creation attempt",
                user_id=current_user.id,
                nfc_id=node.nfc_id,
                house_id=node.house_id)
    
    # Verifica se il nodo esiste già
    query = select(Node).where(Node.nfc_id == node.nfc_id)
    result = safe_exec(session, query)
    existing_node = result.first()
    if existing_node:
        logger.warning("Node creation failed - NFC ID already exists",
                       user_id=current_user.id,
                       nfc_id=node.nfc_id)
        raise HTTPException(
            status_code=400,
            detail="Node with this NFC ID already exists"
        )
    
    # Crea il nuovo nodo
    db_node = Node(**node.model_dump())
    session.add(db_node)
    session.commit()
    session.refresh(db_node)
    
    logger.info("Node created successfully",
                user_id=current_user.id,
                node_id=db_node.id,
                nfc_id=db_node.nfc_id,
                house_id=db_node.house_id)
    
    return db_node

@router.get("/{node_id}", response_model=NodeResponse)
def read_node(
    node_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Recupera un nodo specifico."""
    logger.info("Node read request",
                user_id=current_user.id,
                node_id=node_id)
    
    node = session.get(Node, node_id)
    if not node:
        logger.warning("Node not found",
                       user_id=current_user.id,
                       node_id=node_id)
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    
    logger.info("Node retrieved successfully",
                user_id=current_user.id,
                node_id=node_id,
                nfc_id=node.nfc_id)
    
    return node

@router.put("/{node_id}", response_model=NodeResponse)
def update_node(
    node_id: int,
    node_update: NodeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un nodo esistente."""
    logger.info("Node update attempt",
                user_id=current_user.id,
                node_id=node_id,
                nfc_id=node_update.nfc_id)
    
    db_node = session.get(Node, node_id)
    if not db_node:
        logger.warning("Node update failed - node not found",
                       user_id=current_user.id,
                       node_id=node_id)
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    
    node_data = node_update.model_dump(exclude_unset=True)
    for key, value in node_data.items():
        setattr(db_node, key, value)
    
    session.add(db_node)
    session.commit()
    session.refresh(db_node)
    
    logger.info("Node updated successfully",
                user_id=current_user.id,
                node_id=node_id,
                nfc_id=db_node.nfc_id)
    
    return db_node

@router.delete("/{node_id}")
def delete_node(
    node_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Elimina un nodo."""
    logger.info("Node deletion attempt",
                user_id=current_user.id,
                node_id=node_id)
    
    db_node = session.get(Node, node_id)
    if not db_node:
        logger.warning("Node deletion failed - node not found",
                       user_id=current_user.id,
                       node_id=node_id)
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    
    nfc_id = db_node.nfc_id
    house_id = db_node.house_id
    
    session.delete(db_node)
    session.commit()
    
    logger.info("Node deleted successfully",
                user_id=current_user.id,
                node_id=node_id,
                nfc_id=nfc_id,
                house_id=house_id)
    
    return {"message": "Nodo eliminato con successo"} 