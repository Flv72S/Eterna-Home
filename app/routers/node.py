from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.models.node import Node, NodeCreate
from app.models.user import User
from app.database import get_session
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=Node)
def create_node(
    node: NodeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuovo nodo."""
    if not node.house_id:
        raise HTTPException(status_code=400, detail="house_id è obbligatorio")
    
    # Verifica se esiste già un nodo con lo stesso nfc_id
    existing_node = session.exec(select(Node).where(Node.nfc_id == node.nfc_id)).first()
    if existing_node:
        raise HTTPException(status_code=400, detail="Un nodo con questo nfc_id esiste già")
    
    db_node = Node.model_validate(node)
    session.add(db_node)
    session.commit()
    session.refresh(db_node)
    return db_node

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

@router.get("/", response_model=List[Node])
def read_nodes(
    name: Optional[str] = None,
    nfc_id: Optional[str] = None,
    house_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Recupera una lista di nodi con filtri opzionali."""
    query = select(Node)
    
    if name:
        query = query.where(Node.name.ilike(f"%{name}%"))
    if nfc_id:
        query = query.where(Node.nfc_id.ilike(f"%{nfc_id}%"))
    if house_id:
        query = query.where(Node.house_id == house_id)
    
    nodes = session.exec(query).all()
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