"""
Router amministrativo per l'interfaccia di import BIM da repository pubbliche.
Fornisce l'interfaccia web per la gestione dell'import BIM pubblico.
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
from app.db.utils import safe_exec

# Configurazione del logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/bim/import", response_class=HTMLResponse)
async def admin_bim_import_interface(
    request: Request,
    current_user: User = Depends(require_permission_in_tenant("manage_bim_sources")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Interfaccia amministrativa per l'import BIM da repository pubbliche.
    Richiede permesso 'manage_bim_sources' nel tenant attivo.
    """
    try:
        # Ottieni le case del tenant
        houses_query = select(House).where(House.tenant_id == tenant_id)
        houses = safe_exec(session, houses_query).all()
        
        # Ottieni statistiche BIM del tenant
        from app.models.bim_model import BIMModel
        bim_stats_query = select(BIMModel).where(BIMModel.tenant_id == tenant_id)
        bim_models = safe_exec(session, bim_stats_query).all()
        
        # Calcola statistiche
        total_models = len(bim_models)
        public_models = len([m for m in bim_models if m.project_phase == "imported"])
        ifc_models = len([m for m in bim_models if m.format == "ifc"])
        dxf_models = len([m for m in bim_models if m.format == "dxf"])
        pdf_models = len([m for m in bim_models if m.format == "pdf"])
        
        # Importa il template
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="app/templates")
        
        return templates.TemplateResponse("admin/bim_import.html", {
            "request": request,
            "tenant_id": tenant_id,
            "houses": houses,
            "bim_stats": {
                "total_models": total_models,
                "public_models": public_models,
                "ifc_models": ifc_models,
                "dxf_models": dxf_models,
                "pdf_models": pdf_models
            }
        })
        
    except Exception as e:
        logger.error(f"Errore durante caricamento interfaccia import BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento dell'interfaccia"
        )

@router.get("/bim/import/stats")
async def get_bim_import_stats(
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene statistiche sui modelli BIM importati da repository pubbliche.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        from app.models.bim_model import BIMModel
        
        # Query per modelli importati da fonti pubbliche
        public_models_query = select(BIMModel).where(
            BIMModel.tenant_id == tenant_id,
            BIMModel.project_phase == "imported"
        )
        public_models = safe_exec(session, public_models_query).all()
        
        # Statistiche per fonte
        source_stats = {}
        for model in public_models:
            source = model.project_organization or "unknown"
            if source not in source_stats:
                source_stats[source] = {
                    "count": 0,
                    "total_size": 0,
                    "formats": {}
                }
            source_stats[source]["count"] += 1
            source_stats[source]["total_size"] += model.file_size
            
            format_key = model.format or "unknown"
            if format_key not in source_stats[source]["formats"]:
                source_stats[source]["formats"][format_key] = 0
            source_stats[source]["formats"][format_key] += 1
        
        # Statistiche generali
        total_public_models = len(public_models)
        total_size = sum(m.file_size for m in public_models)
        
        return {
            "total_public_models": total_public_models,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "source_stats": source_stats,
            "recent_imports": [
                {
                    "id": model.id,
                    "name": model.name,
                    "format": model.format,
                    "source": model.project_organization,
                    "imported_at": model.created_at.isoformat(),
                    "file_size": model.file_size
                }
                for model in sorted(public_models, key=lambda x: x.created_at, reverse=True)[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Errore durante recupero statistiche import BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        )

@router.get("/bim/import/history")
async def get_bim_import_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene la cronologia degli import BIM da repository pubbliche.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        from app.models.bim_model import BIMModel
        from sqlmodel import func
        
        # Query per modelli importati da fonti pubbliche con paginazione
        public_models_query = (
            select(BIMModel)
            .where(
                BIMModel.tenant_id == tenant_id,
                BIMModel.project_phase == "imported"
            )
            .order_by(BIMModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        public_models = safe_exec(session, public_models_query).all()
        
        # Query per contare totale
        total_query = select(func.count(BIMModel.id)).where(
            BIMModel.tenant_id == tenant_id,
            BIMModel.project_phase == "imported"
        )
        total = safe_exec(session, total_query).first()
        
        return {
            "items": [
                {
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "format": model.format,
                    "source_repository": model.project_organization,
                    "source_url": model.project_author,
                    "file_size": model.file_size,
                    "imported_at": model.created_at.isoformat(),
                    "house_id": model.house_id,
                    "user_id": model.user_id
                }
                for model in public_models
            ],
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"Errore durante recupero cronologia import BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della cronologia"
        ) 