"""
Router per la gestione dei manuali PDF degli oggetti domestici.
Estende il sistema documenti esistente con funzionalità specifiche per manuali.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
import uuid
import hashlib
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant, require_house_access
from app.models.user import User
from app.models.document import Document
from app.models.house import House
from app.models.room import Room
from app.models.node import Node
from app.schemas.document import DocumentCreate, DocumentRead
from app.services.minio_service import get_minio_service
from app.db.utils import safe_exec
from app.security.validators import validate_file_upload, sanitize_filename, TextValidator
from app.utils.security import log_security_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manuals", tags=["Manuals"])

@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
@require_house_access("house_id")
async def upload_manual_pdf(
    file: UploadFile = File(...),
    device_name: str = Form(..., description="Nome dell'oggetto/elettrodomestico"),
    brand: str = Form(..., description="Marca dell'oggetto"),
    model: str = Form(..., description="Modello dell'oggetto"),
    description: Optional[str] = Form(None, description="Descrizione del manuale"),
    house_id: int = Form(...),
    room_id: Optional[int] = Form(None, description="ID della stanza associata"),
    node_id: Optional[int] = Form(None, description="ID del nodo associato"),
    current_user: User = Depends(require_permission_in_tenant("write_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Carica un manuale PDF per un oggetto domestico.
    Richiede permesso 'write_documents' nel tenant attivo.
    """
    try:
        # Validazione file PDF
        allowed_types = ["application/pdf"]
        max_size = 50 * 1024 * 1024  # 50MB per manuali PDF
        
        # Sanifica e valida il file
        safe_filename = sanitize_filename(file.filename)
        validate_file_upload(file, allowed_types, max_size)
        
        # Validazione campi testo
        device_name = TextValidator.validate_text_field(device_name, "device_name", max_length=255)
        brand = TextValidator.validate_text_field(brand, "brand", max_length=100)
        model = TextValidator.validate_text_field(model, "model", max_length=100)
        if description:
            description = TextValidator.validate_text_field(description, "description", max_length=1000)
        
        # Verifica che la stanza esista e appartenga alla casa se specificata
        if room_id:
            room_query = select(Room).where(
                Room.id == room_id,
                Room.house_id == house_id
            )
            room = session.exec(room_query).first()
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stanza non trovata o non associata alla casa"
                )
        
        # Verifica che il nodo esista e appartenga alla casa se specificato
        if node_id:
            node_query = select(Node).where(
                Node.id == node_id,
                Node.house_id == house_id
            )
            node = session.exec(node_query).first()
            if not node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nodo non trovato o non associato alla casa"
                )
        
        # Calcola checksum
        content = await file.read()
        checksum = hashlib.sha256(content).hexdigest()
        
        # Genera nome file sicuro
        file_extension = os.path.splitext(safe_filename)[1]
        manual_filename = f"{brand}_{model}_{device_name}{file_extension}".replace(" ", "_")
        manual_filename = sanitize_filename(manual_filename)
        
        # Carica su MinIO con path specifico per manuali
        minio_service = get_minio_service()
        
        # Determina il path di storage
        if room_id:
            storage_path = f"tenants/{tenant_id}/houses/{house_id}/manuals/rooms/{room_id}/{manual_filename}"
        elif node_id:
            storage_path = f"tenants/{tenant_id}/houses/{house_id}/manuals/nodes/{node_id}/{manual_filename}"
        else:
            storage_path = f"tenants/{tenant_id}/houses/{house_id}/manuals/{manual_filename}"
        
        # Simula upload in modalità sviluppo
        if not minio_service.client:
            logger.info(f"[DEV] Simulazione upload manuale: {storage_path}")
            upload_result = {
                "filename": manual_filename,
                "original_filename": file.filename,
                "storage_path": storage_path,
                "file_size": len(content),
                "content_type": file.content_type,
                "tenant_id": str(tenant_id),
                "house_id": house_id,
                "folder": "manuals",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "is_encrypted": False,
                "dev_mode": True
            }
        else:
            # Upload reale su MinIO
            upload_result = await minio_service.upload_file(
                file=file,
                folder="manuals",
                tenant_id=tenant_id,
                house_id=house_id
            )
        
        # Crea record nel database
        document_data = DocumentCreate(
            title=f"Manuale {device_name} {brand} {model}",
            description=description or f"Manuale per {device_name} {brand} {model}",
            document_type="manual",
            file_url=upload_result["storage_path"],
            file_size=len(content),
            file_type=file.content_type,
            checksum=checksum,
            house_id=house_id,
            node_id=node_id,
            device_name=device_name,
            brand=brand,
            model=model,
            room_id=room_id
        )
        
        document = Document(**document_data.model_dump())
        document.owner_id = current_user.id
        document.tenant_id = tenant_id
        
        session.add(document)
        session.commit()
        session.refresh(document)
        
        # Log evento di sicurezza
        log_security_event(
            event_type="manual_upload",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "device_name": device_name,
                "brand": brand,
                "model": model,
                "file_size": len(content),
                "filename": manual_filename,
                "house_id": house_id,
                "room_id": room_id,
                "node_id": node_id,
                "upload_success": True
            }
        )
        
        logger.info(
            f"Manuale PDF caricato con successo: {device_name} {brand} {model} "
            f"(tenant: {tenant_id}, house: {house_id}, room: {room_id}, node: {node_id})"
        )
        
        return DocumentRead.model_validate(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MANUALS] Errore durante upload manuale PDF: {e}")
        
        # Log evento di sicurezza per errore
        log_security_event(
            event_type="manual_upload_failed",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "device_name": device_name if 'device_name' in locals() else None,
                "brand": brand if 'brand' in locals() else None,
                "model": model if 'model' in locals() else None,
                "error": str(e),
                "upload_success": False
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento del manuale PDF"
        )

@router.post("/link", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
@require_house_access("house_id")
async def add_manual_link(
    external_link: str = Form(..., description="Link esterno al manuale PDF"),
    device_name: str = Form(..., description="Nome dell'oggetto/elettrodomestico"),
    brand: str = Form(..., description="Marca dell'oggetto"),
    model: str = Form(..., description="Modello dell'oggetto"),
    description: Optional[str] = Form(None, description="Descrizione del manuale"),
    house_id: int = Form(...),
    room_id: Optional[int] = Form(None, description="ID della stanza associata"),
    node_id: Optional[int] = Form(None, description="ID del nodo associato"),
    current_user: User = Depends(require_permission_in_tenant("write_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Aggiunge un link esterno a un manuale PDF.
    Richiede permesso 'write_documents' nel tenant attivo.
    """
    try:
        # Validazione URL
        if not external_link or not external_link.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link esterno non può essere vuoto"
            )
        
        parsed_url = urlparse(external_link)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL non valido"
            )
        
        # Validazione campi testo
        device_name = TextValidator.validate_text_field(device_name, "device_name", max_length=255)
        brand = TextValidator.validate_text_field(brand, "brand", max_length=100)
        model = TextValidator.validate_text_field(model, "model", max_length=100)
        if description:
            description = TextValidator.validate_text_field(description, "description", max_length=1000)
        
        # Verifica che la stanza esista e appartenga alla casa se specificata
        if room_id:
            room_query = select(Room).where(
                Room.id == room_id,
                Room.house_id == house_id
            )
            room = session.exec(room_query).first()
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stanza non trovata o non associata alla casa"
                )
        
        # Verifica che il nodo esista e appartenga alla casa se specificato
        if node_id:
            node_query = select(Node).where(
                Node.id == node_id,
                Node.house_id == house_id
            )
            node = session.exec(node_query).first()
            if not node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nodo non trovato o non associato alla casa"
                )
        
        # Crea record nel database (senza file fisico)
        document_data = DocumentCreate(
            title=f"Manuale {device_name} {brand} {model} (Link)",
            description=description or f"Link al manuale per {device_name} {brand} {model}",
            document_type="manual",
            file_url="",  # Vuoto per link esterni
            file_size=0,
            file_type="application/pdf",
            checksum="",  # Vuoto per link esterni
            house_id=house_id,
            node_id=node_id,
            device_name=device_name,
            brand=brand,
            model=model,
            external_link=external_link,
            room_id=room_id
        )
        
        document = Document(**document_data.model_dump())
        document.owner_id = current_user.id
        document.tenant_id = tenant_id
        
        session.add(document)
        session.commit()
        session.refresh(document)
        
        # Log evento di sicurezza
        log_security_event(
            event_type="manual_link_added",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "device_name": device_name,
                "brand": brand,
                "model": model,
                "external_link": external_link,
                "house_id": house_id,
                "room_id": room_id,
                "node_id": node_id,
                "link_success": True
            }
        )
        
        logger.info(
            f"Link manuale aggiunto con successo: {device_name} {brand} {model} "
            f"(tenant: {tenant_id}, house: {house_id})"
        )
        
        return DocumentRead.model_validate(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MANUALS] Errore durante aggiunta link manuale: {e}")
        
        # Log evento di sicurezza per errore
        log_security_event(
            event_type="manual_link_failed",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "device_name": device_name if 'device_name' in locals() else None,
                "brand": brand if 'brand' in locals() else None,
                "model": model if 'model' in locals() else None,
                "external_link": external_link if 'external_link' in locals() else None,
                "error": str(e),
                "link_success": False
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiunta del link al manuale"
        )

@router.get("/", response_model=List[DocumentRead])
async def list_manuals(
    skip: int = 0,
    limit: int = 100,
    house_id: Optional[int] = None,
    room_id: Optional[int] = None,
    node_id: Optional[int] = None,
    brand: Optional[str] = None,
    device_type: Optional[str] = None,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Lista i manuali PDF del tenant corrente.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Query base per manuali del tenant
        query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.document_type == "manual"
        )
        
        # Filtri opzionali
        if house_id:
            query = query.where(Document.house_id == house_id)
        if room_id:
            query = query.where(Document.room_id == room_id)
        if node_id:
            query = query.where(Document.node_id == node_id)
        if brand:
            query = query.where(Document.brand.ilike(f"%{brand}%"))
        if device_type:
            query = query.where(Document.device_name.ilike(f"%{device_type}%"))
        
        # Paginazione
        query = query.offset(skip).limit(limit).order_by(Document.created_at.desc())
        
        manuals = safe_exec(session, query).all()
        
        logger.info(
            f"Lista manuali recuperata: {len(manuals)} manuali "
            f"(tenant: {tenant_id}, house: {house_id})"
        )
        
        return [DocumentRead.model_validate(manual) for manual in manuals]
        
    except Exception as e:
        logger.error(f"[MANUALS] Errore durante listaggio manuali: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei manuali"
        )

@router.get("/stats")
async def get_manuals_stats(
    house_id: Optional[int] = None,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene statistiche sui manuali PDF.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Query base per manuali del tenant
        base_query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.document_type == "manual"
        )
        
        if house_id:
            base_query = base_query.where(Document.house_id == house_id)
        
        # Statistiche generali
        total_manuals = len(safe_exec(session, base_query).all())
        
        # Statistiche per marca
        brand_stats_query = (
            select(Document.brand, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.brand.is_not(None)
            )
        )
        if house_id:
            brand_stats_query = brand_stats_query.where(Document.house_id == house_id)
        brand_stats_query = brand_stats_query.group_by(Document.brand)
        
        brand_stats = safe_exec(session, brand_stats_query).all()
        
        # Statistiche per tipo di dispositivo
        device_stats_query = (
            select(Document.device_name, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.device_name.is_not(None)
            )
        )
        if house_id:
            device_stats_query = device_stats_query.where(Document.house_id == house_id)
        device_stats_query = device_stats_query.group_by(Document.device_name)
        
        device_stats = safe_exec(session, device_stats_query).all()
        
        # Statistiche per tipo (upload vs link)
        upload_count = len(safe_exec(session, base_query.where(Document.file_url != "")).all())
        link_count = len(safe_exec(session, base_query.where(Document.external_link.is_not(None))).all())
        
        return {
            "total_manuals": total_manuals,
            "uploaded_manuals": upload_count,
            "linked_manuals": link_count,
            "brand_stats": [{"brand": brand, "count": count} for brand, count in brand_stats],
            "device_stats": [{"device": device, "count": count} for device, count in device_stats]
        }
        
    except Exception as e:
        logger.error(f"[MANUALS] Errore durante recupero statistiche: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        ) 