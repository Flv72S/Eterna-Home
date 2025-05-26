import uuid
from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import get_db
from backend.utils.auth import get_current_user
from backend.config.cloud_config import settings
from backend.utils.minio import get_minio_client, upload_file_to_minio
from backend.models.legacy_documents import LegacyDocument
from backend.schemas.legacy_documents import LegacyDocument as LegacyDocumentSchema

router = APIRouter(prefix="/legacy-documents", tags=["Legacy Documents"])

@router.post("/", response_model=LegacyDocumentSchema)
async def create_legacy_document(
    house_id: int = Form(...),
    node_id: int = Form(...),
    type: str = Form(...),
    version: str = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Inizializza il client MinIO
    minio_client = get_minio_client()
    
    # Genera un nome unico per il file
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Leggi il contenuto del file
    file_content = await file.read()
    
    # Carica il file su MinIO
    file_url = await upload_file_to_minio(
        minio_client,
        settings.MINIO_BUCKET_LEGACY,
        unique_filename,
        file_content,
        file.content_type
    )
    
    # Crea il nuovo documento nel database
    db_document = LegacyDocument(
        house_id=house_id,
        node_id=node_id,
        type=type,
        version=version,
        file_url=file_url
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document

@router.get("/{node_id}", response_model=List[LegacyDocumentSchema])
async def get_legacy_documents(
    node_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(LegacyDocument).filter(LegacyDocument.node_id == node_id).all()
    return documents 