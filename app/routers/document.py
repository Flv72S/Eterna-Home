"""
Router per la gestione dei documenti con supporto multi-tenant e multi-house.
Integra path dinamici basati su tenant_id e house_id per isolamento completo.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, and_
import uuid
import io
import hashlib
import os
from datetime import datetime, timezone

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant, require_house_access
from app.models.user import User
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.house import House
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentRead
)
from app.services.minio_service import get_minio_service
from app.db.utils import safe_exec
from app.core.logging_multi_tenant import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentRead)
@require_house_access("house_id")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_type: Optional[str] = Form("general"),
    house_id: int = Form(...),
    current_user: User = Depends(require_permission_in_tenant("write_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Carica un nuovo documento nel tenant corrente per una casa specifica.
    Richiede permesso 'write_documents' nel tenant attivo e accesso alla casa.
    """
    try:
        # Verifica che la casa esista e appartenga al tenant
        house = session.get(House, house_id)
        if not house or house.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Casa non trovata o non appartiene al tenant"
            )
        
        # Carica il file su MinIO con path multi-tenant e multi-house
        minio_service = get_minio_service()
        upload_result = minio_service.upload_file(
            file=file,
            folder=f"houses/{house_id}/documents",
            tenant_id=tenant_id,
            house_id=house_id
        )
        
        # Crea il record del documento nel database
        document_data = DocumentCreate(
            title=title,
            description=description,
            document_type=document_type,
            file_path=upload_result["storage_path"],
            file_size=upload_result["file_size"],
            file_type=upload_result["content_type"],
            tenant_id=tenant_id,
            house_id=house_id,
            owner_id=current_user.id
        )
        
        document = Document.from_orm(document_data)
        session.add(document)
        session.commit()
        session.refresh(document)
        
        logger.info(
            "Documento caricato con successo",
            extra={
                "user_id": current_user.id,
                "house_id": house_id,
                "tenant_id": tenant_id,
                "document_id": document.id,
                "file_size": upload_result["file_size"]
            }
        )
        
        return DocumentRead.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante upload documento",
            extra={
                "user_id": current_user.id,
                "house_id": house_id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento del documento"
        )

@router.get("/", response_model=List[DocumentRead])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    house_id: Optional[int] = Query(None, description="Filtra per ID casa"),
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Lista i documenti del tenant corrente.
    Se house_id è specificato, filtra solo per quella casa e verifica l'accesso.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Query base filtrata per tenant
        query = select(Document).where(Document.tenant_id == tenant_id)
        
        # Filtro per casa se specificato
        if house_id:
            # Verifica accesso alla casa
            if not current_user.has_house_access(house_id, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non hai accesso a questa casa"
                )
            query = query.where(Document.house_id == house_id)
        else:
            # Se non è specificata una casa, mostra solo documenti delle case a cui l'utente ha accesso
            user_house_ids = current_user.get_house_ids(tenant_id)
            if user_house_ids:
                query = query.where(Document.house_id.in_(user_house_ids))
            else:
                # Se l'utente non ha accesso a nessuna casa, restituisci lista vuota
                return []
        
        # Filtro per tipo di documento se specificato
        if document_type:
            query = query.where(Document.document_type == document_type)
        
        # Paginazione
        query = query.offset(skip).limit(limit)
        
        # Esegui query
        documents = safe_exec(session, query).all()
        
        logger.info(
            "Lista documenti recuperata",
            extra={
                "user_id": current_user.id,
                "house_id": house_id,
                "tenant_id": tenant_id,
                "total_documents": len(documents)
            }
        )
        
        return [DocumentRead.from_orm(doc) for doc in documents]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante listaggio documenti",
            extra={
                "user_id": current_user.id,
                "house_id": house_id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei documenti"
        )

@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene un documento specifico del tenant corrente.
    Verifica automaticamente l'accesso alla casa associata al documento.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        
        document = safe_exec(session, query).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato"
            )
        
        # Verifica accesso alla casa del documento
        if not current_user.has_house_access(document.house_id, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai accesso alla casa di questo documento"
            )
        
        logger.info(
            "Documento recuperato",
            extra={
                "user_id": current_user.id,
                "document_id": document_id,
                "house_id": document.house_id,
                "tenant_id": tenant_id
            }
        )
        
        return DocumentRead.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante recupero documento",
            extra={
                "user_id": current_user.id,
                "document_id": document_id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del documento"
        )

@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Scarica un documento del tenant corrente.
    Verifica automaticamente l'accesso alla casa associata al documento.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Ottieni il documento dal database
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        
        document = safe_exec(session, query).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato"
            )
        
        # Verifica accesso alla casa del documento
        if not current_user.has_house_access(document.house_id, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai accesso alla casa di questo documento"
            )
        
        # Scarica il file da MinIO
        minio_service = get_minio_service()
        file_data = minio_service.download_file(
            storage_path=document.file_path,
            tenant_id=tenant_id,
            house_id=document.house_id
        )
        
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File non trovato nello storage"
            )
        
        logger.info(
            "Documento scaricato",
            extra={
                "user_id": current_user.id,
                "document_id": document_id,
                "house_id": document.house_id,
                "tenant_id": tenant_id,
                "file_size": file_data["file_size"]
            }
        )
        
        # Crea response di streaming
        return StreamingResponse(
            io.BytesIO(file_data["content"]),
            media_type=file_data["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={file_data['filename']}",
                "Content-Length": str(file_data["file_size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante download documento",
            extra={
                "user_id": current_user.id,
                "document_id": document_id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il download del documento"
        )

@router.put("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(require_permission_in_tenant("write_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un documento del tenant corrente.
    Richiede permesso 'write_documents' nel tenant attivo.
    """
    try:
        # Ottieni il documento dal database
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        
        document = safe_exec(session, query).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato"
            )
        
        # Aggiorna i campi del documento
        update_data = document_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        
        session.add(document)
        session.commit()
        session.refresh(document)
        
        return DocumentRead.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOCUMENT] Errore durante aggiornamento documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento del documento"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(require_permission_in_tenant("delete_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Elimina un documento del tenant corrente.
    Richiede permesso 'delete_documents' nel tenant attivo.
    """
    try:
        # Ottieni il documento dal database
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        
        document = safe_exec(session, query).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato"
            )
        
        # Elimina il file da MinIO
        minio_service.delete_file(
            storage_path=document.file_path,
            tenant_id=tenant_id
        )
        
        # Elimina il record dal database
        session.delete(document)
        session.commit()
        
        return {"message": "Documento eliminato con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOCUMENT] Errore durante eliminazione documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'eliminazione del documento"
        )

@router.get("/{document_id}/presigned-url")
async def get_document_presigned_url(
    document_id: int,
    expires: int = 3600,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene un URL pre-firmato per accedere al documento.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Ottieni il documento dal database
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        
        document = safe_exec(session, query).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato"
            )
        
        # Crea URL pre-firmato
        presigned_url = minio_service.create_presigned_url(
            storage_path=document.file_path,
            tenant_id=tenant_id,
            method="GET",
            expires=expires
        )
        
        return {
            "presigned_url": presigned_url,
            "expires_in": expires,
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOCUMENT] Errore durante creazione URL pre-firmato: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la creazione dell'URL"
        )

@router.get("/storage/info")
async def get_storage_info(
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene informazioni sullo storage del tenant corrente.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Lista i file nella cartella documents del tenant
        files = minio_service.list_files(
            folder="documents",
            tenant_id=tenant_id
        )
        
        # Calcola statistiche
        total_files = len(files)
        total_size = sum(file["file_size"] for file in files)
        
        return {
            "tenant_id": str(tenant_id),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": files
        }
        
    except Exception as e:
        print(f"[DOCUMENT] Errore durante recupero info storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle informazioni dello storage"
        )

# TODO: Implementare endpoint per upload multipli
# TODO: Aggiungere endpoint per ricerca documenti
# TODO: Implementare versioning dei documenti
# TODO: Aggiungere endpoint per condivisione documenti tra utenti dello stesso tenant 