from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import List
import io

from app.core.deps import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.document import Document
from app.core.storage.minio import minio_client

router = APIRouter()

@router.post("/{document_id}/upload")
async def upload_document_file(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Carica un file associato a un documento.
    """
    # Verifica che il documento esista
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    # Verifica che l'utente abbia accesso alla casa
    if document.house.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai i permessi per accedere a questo documento"
        )
    
    # Verifica che non ci sia già un file caricato
    if document.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il documento ha già un file associato"
        )
    
    # Carica il file su MinIO
    file_path, checksum = await minio_client.upload_file(
        file=file,
        house_id=document.house_id,
        document_id=document.id
    )
    
    # Aggiorna il documento nel database
    document.file_path = file_path
    document.checksum = checksum
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {
        "message": "File caricato con successo",
        "file_path": file_path,
        "checksum": checksum
    }

@router.get("/{document_id}/download")
async def download_document_file(
    document_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Scarica il file associato a un documento.
    """
    # Verifica che il documento esista
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento non trovato"
        )
    
    # Verifica che l'utente abbia accesso alla casa
    if document.house.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai i permessi per accedere a questo documento"
        )
    
    # Verifica che il file esista
    if not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun file associato al documento"
        )
    
    # Scarica il file da MinIO
    file_content = minio_client.download_file(document.file_path)
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File non trovato su MinIO"
        )
    
    # Restituisci il file come streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{document.title}"'
        }
    ) 