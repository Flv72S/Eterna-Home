from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.models.node import Node, NodeCreate
from app.models.user import User
from app.database import get_session
from app.utils.security import get_current_user
from app.core.deps import get_session
from app.db.utils import safe_exec
from app.schemas.node import NodeResponse

router = APIRouter()

@router.post("/", response_model=NodeResponse)
async def create_node(
    node: NodeCreate,
    session: Session = Depends(get_session)
):
    """Crea un nuovo nodo."""
    # Verifica se il nodo esiste già
    query = select(Node).where(Node.nfc_id == node.nfc_id)
    result = safe_exec(session, query)
    existing_node = result.first()
    if existing_node:
        raise HTTPException(
            status_code=400,
            detail="Node with this NFC ID already exists"
        )

@router.get("/{node_id}", response_model=Node)
def read_node(
    node_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Recupera un nodo specifico."""
    node = session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    return node

@router.get("/", response_model=List[NodeResponse])
async def read_nodes(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Ottiene la lista dei nodi."""
    query = select(Node).offset(skip).limit(limit)
    result = safe_exec(session, query)
    nodes = result.all()
    return nodes

@router.put("/{node_id}", response_model=Node)
def update_node(
    node_id: int,
    node_update: Node,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un nodo esistente."""
    db_node = session.get(Node, node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    
    node_data = node_update.model_dump(exclude_unset=True)
    for key, value in node_data.items():
        setattr(db_node, key, value)
    
    session.add(db_node)
    session.commit()
    session.refresh(db_node)
    return db_node

@router.delete("/{node_id}")
def delete_node(
    node_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Elimina un nodo."""
    db_node = session.get(Node, node_id)
    if not db_node:
        raise HTTPException(status_code=404, detail="Nodo non trovato")
    
    session.delete(db_node)
    session.commit()
    return {"message": "Nodo eliminato con successo"} 