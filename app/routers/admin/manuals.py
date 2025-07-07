"""
Router amministrativo per la gestione dei manuali PDF.
Fornisce l'interfaccia web per la gestione dei manuali degli oggetti domestici.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
import uuid

from app.core.deps import get_current_user, get_current_tenant, get_session
from app.core.auth.rbac import require_permission_in_tenant
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.db.utils import safe_exec

# Configurazione del logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/manuals", response_class=HTMLResponse)
async def admin_manuals_interface(
    request: Request,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Interfaccia amministrativa per la gestione dei manuali PDF.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        # Ottieni le case del tenant
        houses_query = select(House).where(House.tenant_id == tenant_id)
        houses = safe_exec(session, houses_query).all()
        
        # Ottieni statistiche manuali del tenant
        manuals_query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.document_type == "manual"
        )
        manuals = safe_exec(session, manuals_query).all()
        
        # Calcola statistiche
        total_manuals = len(manuals)
        uploaded_manuals = len([m for m in manuals if m.file_url and m.file_url.strip()])
        linked_manuals = len([m for m in manuals if m.external_link])
        
        # Statistiche per marca
        brand_stats = {}
        for manual in manuals:
            if manual.brand:
                if manual.brand not in brand_stats:
                    brand_stats[manual.brand] = 0
                brand_stats[manual.brand] += 1
        
        # Statistiche per tipo di dispositivo
        device_stats = {}
        for manual in manuals:
            if manual.device_name:
                if manual.device_name not in device_stats:
                    device_stats[manual.device_name] = 0
                device_stats[manual.device_name] += 1
        
        # Importa il template
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="app/templates")
        
        return templates.TemplateResponse("admin/manuals/index.html", {
            "request": request,
            "tenant_id": tenant_id,
            "houses": houses,
            "manual_stats": {
                "total_manuals": total_manuals,
                "uploaded_manuals": uploaded_manuals,
                "linked_manuals": linked_manuals,
                "brand_stats": brand_stats,
                "device_stats": device_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Errore durante caricamento interfaccia manuali: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento dell'interfaccia"
        )

@router.get("/manuals/stats")
async def get_manuals_stats(
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene statistiche dettagliate sui manuali PDF.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Query per manuali del tenant
        manuals_query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.document_type == "manual"
        )
        manuals = safe_exec(session, manuals_query).all()
        
        # Statistiche generali
        total_manuals = len(manuals)
        uploaded_manuals = len([m for m in manuals if m.file_url and m.file_url.strip()])
        linked_manuals = len([m for m in manuals if m.external_link])
        
        # Statistiche per marca
        brand_stats_query = (
            select(Document.brand, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.brand.is_not(None)
            )
            .group_by(Document.brand)
        )
        brand_stats = safe_exec(session, brand_stats_query).all()
        
        # Statistiche per tipo di dispositivo
        device_stats_query = (
            select(Document.device_name, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.device_name.is_not(None)
            )
            .group_by(Document.device_name)
        )
        device_stats = safe_exec(session, device_stats_query).all()
        
        # Statistiche per casa
        house_stats_query = (
            select(Document.house_id, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.house_id.is_not(None)
            )
            .group_by(Document.house_id)
        )
        house_stats = safe_exec(session, house_stats_query).all()
        
        # Statistiche per stanza
        room_stats_query = (
            select(Document.room_id, func.count(Document.id))
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual",
                Document.room_id.is_not(None)
            )
            .group_by(Document.room_id)
        )
        room_stats = safe_exec(session, room_stats_query).all()
        
        return {
            "total_manuals": total_manuals,
            "uploaded_manuals": uploaded_manuals,
            "linked_manuals": linked_manuals,
            "brand_stats": [{"brand": brand, "count": count} for brand, count in brand_stats],
            "device_stats": [{"device": device, "count": count} for device, count in device_stats],
            "house_stats": [{"house_id": house_id, "count": count} for house_id, count in house_stats],
            "room_stats": [{"room_id": room_id, "count": count} for room_id, count in room_stats],
            "recent_manuals": [
                {
                    "id": manual.id,
                    "device_name": manual.device_name,
                    "brand": manual.brand,
                    "model": manual.model,
                    "type": "upload" if manual.file_url else "link",
                    "created_at": manual.created_at.isoformat(),
                    "house_id": manual.house_id
                }
                for manual in sorted(manuals, key=lambda x: x.created_at, reverse=True)[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Errore durante recupero statistiche manuali: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        )

@router.get("/manuals/history")
async def get_manuals_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_permission_in_tenant("read_documents")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene la cronologia dei manuali PDF.
    Richiede permesso 'read_documents' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Query per manuali del tenant con paginazione
        manuals_query = (
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.document_type == "manual"
            )
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        manuals = safe_exec(session, manuals_query).all()
        
        # Query per contare totale
        total_query = select(func.count(Document.id)).where(
            Document.tenant_id == tenant_id,
            Document.document_type == "manual"
        )
        total = safe_exec(session, total_query).first()
        
        return {
            "items": [
                {
                    "id": manual.id,
                    "device_name": manual.device_name,
                    "brand": manual.brand,
                    "model": manual.model,
                    "description": manual.description,
                    "type": "upload" if manual.file_url else "link",
                    "file_size": manual.file_size,
                    "external_link": manual.external_link,
                    "house_id": manual.house_id,
                    "room_id": manual.room_id,
                    "node_id": manual.node_id,
                    "created_at": manual.created_at.isoformat(),
                    "owner_id": manual.owner_id
                }
                for manual in manuals
            ],
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Errore durante recupero cronologia manuali: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della cronologia"
        ) 