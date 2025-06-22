from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlmodel import Session, select, or_
from app.utils.security import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.db import get_session
from app.services.minio_service import MinioService, get_minio_service
from app.core.config import settings
import uuid
import hashlib

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=DocumentRead)
def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new document"""
    db_document = Document(
        **document.model_dump(),
        owner_id=current_user.id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.get("/{document_id}", response_model=DocumentRead)
def read_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get a specific document by ID"""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per accedere a questo documento")
    
    return document

@router.get("/", response_model=List[DocumentRead])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    house_id: Optional[int] = None,
    node_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get list of documents with optional filtering and search"""
    query = select(Document).where(Document.owner_id == current_user.id)
    
    if house_id:
        query = query.where(Document.house_id == house_id)
    if node_id:
        query = query.where(Document.node_id == node_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Document.name.ilike(search_term),
                Document.description.ilike(search_term)
            )
        )
    
    query = query.offset(skip).limit(limit)
    
    return db.exec(query).all()

@router.put("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: int,
    document: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update a document"""
    db_document = db.get(Document, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if db_document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per modificare questo documento")
    
    document_data = document.model_dump(exclude_unset=True)
    for key, value in document_data.items():
        setattr(db_document, key, value)
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a document"""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per eliminare questo documento")
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    minio_service: MinioService = Depends(get_minio_service)
):
    """Download a document by ID."""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per scaricare questo documento")
    
    try:
        download_url = minio_service.get_presigned_get_url(document.path)
        return {"download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating download URL")

@router.post("/{document_id}/upload")
async def upload_document_file(
    document_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    minio_service: MinioService = Depends(get_minio_service)
):
    """Upload a file to an existing document."""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai i permessi per caricare file su questo documento")
    
    try:
        # Genera un nome file unico
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"/documents/{unique_filename}"
        
        # Carica il file su MinIO
        file_content = await file.read()
        minio_service.upload_file(file_path, file_content, file.content_type)
        
        # Aggiorna il documento con il nuovo path
        document.path = file_path
        document.size = len(file_content)
        document.checksum = hashlib.sha256(file_content).hexdigest()
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "message": "File uploaded successfully", 
            "path": file_path,
            "checksum": document.checksum
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}") 