from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os

from backend.db.session import get_db
from backend.models.document import Document
from backend.models.node import Node
from backend.models.house import House
from backend.models.user import User
from backend.schemas.document import DocumentCreate, Document as DocumentSchema
from backend.utils.auth import get_current_user
from backend.utils.minio import upload_file, get_file_url

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/", response_model=DocumentSchema)
async def create_document(
    document: DocumentCreate,
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verifica che il nodo esista e appartenga a una casa dell'utente
    node = db.query(Node).join(House).filter(
        Node.id == document.node_id,
        House.owner_id == current_user.id
    ).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Se è stato fornito un file, lo salva localmente
    file_path = None
    if file:
        file_path = await upload_file(file)

    db_document = Document(**document.dict(), file_path=file_path)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.get("/", response_model=List[DocumentSchema])
def read_documents(
    node_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verifica che il nodo esista e appartenga a una casa dell'utente
    node = db.query(Node).join(House).filter(
        Node.id == node_id,
        House.owner_id == current_user.id
    ).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    documents = db.query(Document).filter(Document.node_id == node_id).offset(skip).limit(limit).all()
    return documents

@router.get("/{document_id}", response_model=DocumentSchema)
def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).join(Node).join(House).filter(
        Document.id == document_id,
        House.owner_id == current_user.id
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).join(Node).join(House).filter(
        Document.id == document_id,
        House.owner_id == current_user.id
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Se c'è un file associato, lo elimina da MinIO
    if document.file_path:
        try:
            os.remove(document.file_path)
        except:
            pass  # Ignora errori nella cancellazione del file
    
    db.delete(document)
    db.commit()
    return None 