from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..schemas.legacy import LegacyDocumentResponse
from ..utils.minio import upload_file_to_minio
from ..utils.auth import get_current_user
from ..config import settings
from ..utils.logger import logger

router = APIRouter()

@router.post("/legacy/documents", response_model=LegacyDocumentResponse)
async def create_legacy_document(
    file: UploadFile = File(...),
    house_id: int = Form(...),
    node_id: int = Form(...),
    type: str = Form(...),
    version: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.debug("=== Inizio create_legacy_document ===")
    logger.debug(f"file type: {type(file)}")
    logger.debug(f"file has 'read': {hasattr(file, 'read')}")
    
    # Verifica che il file sia stato fornito
    if not file:
        raise HTTPException(status_code=400, detail="Nessun file fornito")
    
    # Leggi il contenuto del file
    file_content = await file.read()
    logger.debug(f"file_content type after read: {type(file_content)}")
    logger.debug(f"file_content has 'read': {hasattr(file_content, 'read')}")
    
    # Verifica che il contenuto non sia vuoto
    if not file_content:
        raise HTTPException(status_code=400, detail="Il file è vuoto") 