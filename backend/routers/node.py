from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.models.node import Node
from backend.models.house import House
from backend.models.user import User
from backend.schemas.node import NodeCreate, Node as NodeSchema
from backend.db.session import get_db
from backend.utils.auth import get_current_user, role_required

router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.post("/", response_model=NodeSchema)
def create_node(node: NodeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verifica che la casa esista e appartenga all'utente
    house = db.query(House).filter(House.id == node.house_id, House.owner_id == current_user.id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    db_node = Node(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node

@router.get("/", response_model=List[NodeSchema])
def read_nodes(house_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verifica che la casa esista e appartenga all'utente
    house = db.query(House).filter(House.id == house_id, House.owner_id == current_user.id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    nodes = db.query(Node).filter(Node.house_id == house_id).offset(skip).limit(limit).all()
    return nodes

@router.get("/{node_id}", response_model=NodeSchema)
def read_node(node_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    node = db.query(Node).join(House).filter(
        Node.id == node_id,
        House.owner_id == current_user.id
    ).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    node = db.query(Node).join(House).filter(
        Node.id == node_id,
        House.owner_id == current_user.id
    ).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
    return None 