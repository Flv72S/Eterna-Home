"""
Router per il download di modelli BIM da repository pubbliche (PA).
Integra validazione MIME, sicurezza e logging per importazione da fonti esterne.
"""

import logging
import uuid
import hashlib
import os
import mimetypes
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlmodel import Session, select
from datetime import datetime, timezone
import aiohttp
import tempfile

# Configurazione del logger
logger = logging.getLogger(__name__)

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant
from app.models.user import User
from app.models.bim_model import BIMModel
from app.models.house import House
from app.schemas.bim import BIMModelCreate, BIMModelResponse
from app.services.minio_service import get_minio_service
from app.services.bim_public_import import BIMPublicImportService
from app.services.bim_parser import get_bim_parser_service
from app.db.utils import safe_exec
from app.security.validators import sanitize_filename, TextValidator
from app.utils.security import log_security_event

router = APIRouter(prefix="/api/v1/bim", tags=["BIM Public Import"])

@router.post("/public/download", response_model=BIMModelResponse, status_code=status.HTTP_201_CREATED)
async def download_bim_from_public_repository(
    url: str = Form(..., description="URL del file BIM da scaricare"),
    name: str = Form(None, description="Nome personalizzato per il modello"),
    description: str = Form(None, description="Descrizione del modello"),
    house_id: int = Form(None, description="ID della casa associata"),
    source_repository: str = Form(..., description="Nome del repository di origine (es. 'geoportale_regionale', 'catasto', 'comune')"),
    current_user: User = Depends(require_permission_in_tenant("upload_bim")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Scarica un modello BIM da un repository pubblico e lo associa alla casa attiva.
    Richiede permesso 'upload_bim' nel tenant attivo.
    
    Args:
        url: URL del file BIM da scaricare
        name: Nome personalizzato per il modello (opzionale)
        description: Descrizione del modello (opzionale)
        house_id: ID della casa associata (opzionale)
        source_repository: Nome del repository di origine
    
    Returns:
        BIMModelResponse: Modello BIM creato
    """
    try:
        # Validazione input
        if not url or not url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL non può essere vuoto"
            )
        
        # Validazione campi testo
        if name:
            name = TextValidator.validate_text_field(name, "name", max_length=255)
        if description:
            description = TextValidator.validate_text_field(description, "description", max_length=1000)
        if source_repository:
            source_repository = TextValidator.validate_text_field(source_repository, "source_repository", max_length=100)
        
        # Verifica che la casa esista e appartenga al tenant se specificata
        if house_id:
            house_query = select(House).where(
                House.id == house_id,
                House.tenant_id == tenant_id
            )
            house = safe_exec(session, house_query).first()
            if not house:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Casa non trovata o non accessibile"
                )
        
        # Inizializza servizio di import pubblico
        import_service = BIMPublicImportService()
        
        # Scarica e valida il file
        download_result = await import_service.download_and_validate_file(
            url=url,
            tenant_id=tenant_id,
            house_id=house_id
        )
        
        # Calcola checksum del file scaricato
        file_content = download_result["content"]
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Genera nome file sicuro
        original_filename = download_result["filename"]
        safe_filename = sanitize_filename(original_filename)
        
        # Carica su MinIO con path specifico per file pubblici
        minio_service = get_minio_service()
        storage_path = f"tenants/{tenant_id}/houses/{house_id}/public_bim/{safe_filename}" if house_id else f"tenants/{tenant_id}/public_bim/{safe_filename}"
        
        # Simula upload in modalità sviluppo
        if not minio_service.client:
            logger.info(f"[DEV] Simulazione upload file pubblico: {storage_path}")
            upload_result = {
                "filename": safe_filename,
                "original_filename": original_filename,
                "storage_path": storage_path,
                "file_size": len(file_content),
                "content_type": download_result["content_type"],
                "tenant_id": str(tenant_id),
                "house_id": house_id,
                "folder": "public_bim",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "is_encrypted": False,
                "dev_mode": True
            }
        else:
            # Upload reale su MinIO
            import io
            from fastapi import UploadFile
            
            # Crea un UploadFile temporaneo per il servizio MinIO
            temp_file = UploadFile(
                filename=safe_filename,
                content_type=download_result["content_type"],
                file=io.BytesIO(file_content)
            )
            
            upload_result = await minio_service.upload_file(
                file=temp_file,
                folder="public_bim",
                tenant_id=tenant_id,
                house_id=house_id
            )
        
        # Crea record nel database
        bim_model_data = BIMModelCreate(
            name=name or safe_filename,
            description=description or f"Importato da {source_repository}",
            format=os.path.splitext(safe_filename)[1][1:].lower(),
            file_url=upload_result["storage_path"],
            file_size=len(file_content),
            checksum=checksum,
            user_id=current_user.id,
            house_id=house_id
        )
        
        bim_model = BIMModel(**bim_model_data.model_dump())
        bim_model.tenant_id = tenant_id
        
        # Aggiungi metadati specifici per import pubblico
        bim_model.project_author = f"Repository: {source_repository}"
        bim_model.project_organization = source_repository
        bim_model.project_phase = "imported"
        
        session.add(bim_model)
        session.commit()
        session.refresh(bim_model)
        
        # Parsing automatico dei metadati
        try:
            bim_parser_service = get_bim_parser_service()
            metadata_result = await bim_parser_service.parse_bim_file(bim_model)
            
            if metadata_result.get("parsing_success"):
                # Aggiorna modello con metadati estratti
                for key, value in metadata_result.items():
                    if hasattr(bim_model, key) and key not in ["extracted_at", "parsing_success", "parsing_message"]:
                        setattr(bim_model, key, value)
                
                session.commit()
                session.refresh(bim_model)
                logger.info(f"Metadati estratti con successo per modello BIM {bim_model.id}")
            else:
                logger.warning(f"Parsing metadati fallito per modello BIM {bim_model.id}")
                
        except Exception as e:
            logger.error(f"Errore parsing metadati BIM pubblico: {e}")
        
        # Log evento di sicurezza
        log_security_event(
            event_type="bim_public_import",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "source_url": url,
                "source_repository": source_repository,
                "file_size": len(file_content),
                "filename": safe_filename,
                "house_id": house_id,
                "import_success": True
            }
        )
        
        logger.info(
            f"BIM pubblico importato con successo: {safe_filename} "
            f"(tenant: {tenant_id}, house: {house_id}, source: {source_repository})"
        )
        
        return bim_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BIM Public] Errore durante import BIM pubblico: {e}")
        
        # Log evento di sicurezza per errore
        log_security_event(
            event_type="bim_public_import_failed",
            user_id=current_user.id,
            tenant_id=tenant_id,
            details={
                "source_url": url,
                "source_repository": source_repository,
                "error": str(e),
                "import_success": False
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'importazione del modello BIM pubblico"
        )

@router.get("/public/sources")
async def get_public_bim_sources(
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """
    Ottiene la lista delle fonti pubbliche supportate per l'import BIM.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    sources = [
        {
            "id": "geoportale_regionale",
            "name": "Geoportale Regionale",
            "description": "Repository di modelli BIM regionali",
            "url_pattern": "https://geoportale.regione.*/bim/",
            "supported_formats": ["ifc", "dxf", "pdf"]
        },
        {
            "id": "catasto",
            "name": "Catasto",
            "description": "Modelli BIM del catasto nazionale",
            "url_pattern": "https://www.catasto.it/bim/",
            "supported_formats": ["ifc", "dxf"]
        },
        {
            "id": "comune",
            "name": "Comune",
            "description": "Repository BIM comunali",
            "url_pattern": "https://*.comune.*/bim/",
            "supported_formats": ["ifc", "dxf", "pdf"]
        },
        {
            "id": "custom",
            "name": "URL Personalizzato",
            "description": "Importazione da URL personalizzato",
            "url_pattern": "*",
            "supported_formats": ["ifc", "dxf", "pdf"]
        }
    ]
    
    return {
        "sources": sources,
        "supported_formats": ["ifc", "dxf", "pdf"],
        "max_file_size_mb": 500
    } 