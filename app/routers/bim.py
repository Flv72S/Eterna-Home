"""
Router per la gestione dei modelli BIM con supporto multi-tenant.
Integra path dinamici basati su tenant_id e RBAC per isolamento completo.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
import uuid
import hashlib
import os
from datetime import datetime, timezone

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant
from app.models.user import User
from app.models.bim_model import BIMModel, BIMModelVersion
from app.schemas.bim import (
    BIMModelCreate, BIMModelResponse, BIMModelListResponse,
    BIMConversionRequest, BIMConversionResponse, BIMConversionStatusResponse,
    BIMBatchConversionRequest, BIMBatchConversionResponse,
    BIMModelVersionResponse, BIMModelVersionListResponse,
    BIMMetadataResponse, BIMUploadResponse
)
from app.services.minio_service import get_minio_service
from app.services.bim_parser import bim_parser
from app.workers.conversion_worker import process_bim_model, batch_convert_models, get_conversion_status
from app.db.utils import safe_exec
from app.security.validators import validate_file_upload, sanitize_filename, TextValidator

router = APIRouter(prefix="/api/v1/bim", tags=["BIM Models"])

@router.post("/upload", response_model=BIMUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_bim_model(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    house_id: int = None,
    node_id: int = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_permission_in_tenant("upload_bim")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Carica un modello BIM nel tenant corrente con parsing automatico e versionamento.
    Richiede permesso 'upload_bim' nel tenant attivo.
    """
    try:
        # Validazione avanzata del file
        allowed_types = [
            "application/octet-stream",  # Per file BIM generici
            "model/ifc",
            "application/ifc"
        ]
        max_size = 500 * 1024 * 1024  # 500MB per file BIM
        
        # Sanifica e valida il file
        safe_filename = sanitize_filename(file.filename)
        validate_file_upload(file, allowed_types, max_size)
        
        # Validazione campi testo
        if name:
            name = TextValidator.validate_text_field(name, "name", max_length=255)
        if description:
            description = TextValidator.validate_text_field(description, "description", max_length=1000)
        
        # Calcola checksum
        content = await file.read()
        checksum = hashlib.sha256(content).hexdigest()
        
        # Carica su MinIO con path multi-tenant
        minio_service = get_minio_service()
        upload_result = minio_service.upload_file(
            file=file,
            folder="bim",
            tenant_id=tenant_id
        )
        
        # Crea record nel database con tenant_id
        bim_model_data = BIMModelCreate(
            name=name or safe_filename,
            description=description,
            format=os.path.splitext(safe_filename)[1][1:],
            file_url=upload_result["storage_path"],
            file_size=len(content),
            checksum=checksum,
            user_id=current_user.id,
            house_id=house_id or 1,  # Default house_id se non specificato
            node_id=node_id
        )
        
        bim_model = BIMModel(**bim_model_data.dict())
        bim_model.tenant_id = tenant_id
        session.add(bim_model)
        session.commit()
        session.refresh(bim_model)
        
        # Crea prima versione del modello
        version = BIMModelVersion(
            version_number=1,
            change_description="Versione iniziale",
            change_type="major",
            file_url=upload_result["storage_path"],
            file_size=len(content),
            checksum=checksum,
            bim_model_id=bim_model.id,
            created_by_id=current_user.id,
            tenant_id=tenant_id
        )
        session.add(version)
        session.commit()
        
        # Parsing automatico in background
        metadata = None
        parsing_status = "pending"
        conversion_triggered = False
        
        try:
            # Parsing sincrono per metadati base
            metadata_result = await bim_parser.parse_bim_file(bim_model)
            
            if metadata_result.get("parsing_success"):
                # Aggiorna modello con metadati estratti
                for key, value in metadata_result.items():
                    if hasattr(bim_model, key) and key not in ["extracted_at", "parsing_success", "parsing_message"]:
                        setattr(bim_model, key, value)
                
                # Aggiorna versione con metadati
                for key, value in metadata_result.items():
                    if hasattr(version, key) and key not in ["extracted_at", "parsing_success", "parsing_message"]:
                        setattr(version, key, value)
                
                session.commit()
                session.refresh(bim_model)
                session.refresh(version)
                
                parsing_status = "completed"
                metadata = BIMMetadataResponse(
                    model_id=bim_model.id,
                    **{k: v for k, v in metadata_result.items() if k not in ["extracted_at", "parsing_success", "parsing_message"]},
                    extracted_at=metadata_result.get("extracted_at", datetime.now(timezone.utc)),
                    parsing_success=True,
                    parsing_message=metadata_result.get("parsing_message", "Parsing completato")
                )
            else:
                parsing_status = "failed"
                
        except Exception as e:
            logger.error(f"Errore parsing automatico: {e}")
            parsing_status = "failed"
        
        # Avvia conversione asincrona se supportata
        if bim_model.format in ["ifc", "rvt"]:
            try:
                background_tasks.add_task(process_bim_model.delay, bim_model.id, "auto")
                conversion_triggered = True
            except Exception as e:
                logger.error(f"Errore avvio conversione: {e}")
        
        return BIMUploadResponse(
            model=bim_model,
            metadata=metadata,
            parsing_status=parsing_status,
            conversion_triggered=conversion_triggered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BIM] Errore durante upload modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento del modello BIM"
        )

@router.get("/", response_model=BIMModelListResponse)
async def get_bim_models(
    skip: int = 0,
    limit: int = 100,
    format: Optional[str] = None,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene la lista dei modelli BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Query base filtrata per tenant
        base_query = select(BIMModel).where(BIMModel.tenant_id == tenant_id)
        
        # Filtro per formato se specificato
        if format:
            base_query = base_query.where(BIMModel.format == format)
        
        # Query per contare totale
        total_query = select(func.count(BIMModel.id)).where(
            BIMModel.tenant_id == tenant_id
        )
        if format:
            total_query = total_query.where(BIMModel.format == format)
        
        total = safe_exec(session, total_query).first()
        
        # Query per lista con paginazione
        query = (
            base_query
            .order_by(BIMModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        models = safe_exec(session, query).all()
        
        return {
            "items": models,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"[BIM] Errore durante listaggio modelli BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei modelli BIM"
        )

@router.get("/{model_id}", response_model=BIMModelResponse)
async def get_bim_model(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene un modello BIM specifico del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BIM] Errore durante recupero modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del modello BIM"
        )

@router.get("/{model_id}/versions", response_model=BIMModelVersionListResponse)
async def get_bim_model_versions(
    model_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene le versioni di un modello BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Verifica che il modello esista e appartenga al tenant
        model_query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        model = safe_exec(session, model_query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Query versioni filtrate per tenant
        base_query = select(BIMModelVersion).where(
            BIMModelVersion.bim_model_id == model_id,
            BIMModelVersion.tenant_id == tenant_id
        )
        
        # Query per contare totale
        total_query = select(func.count(BIMModelVersion.id)).where(
            BIMModelVersion.bim_model_id == model_id,
            BIMModelVersion.tenant_id == tenant_id
        )
        total = safe_exec(session, total_query).first()
        
        # Query per lista con paginazione
        query = (
            base_query
            .order_by(BIMModelVersion.version_number.desc())
            .offset(skip)
            .limit(limit)
        )
        
        versions = safe_exec(session, query).all()
        
        return {
            "items": versions,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BIM] Errore durante recupero versioni BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle versioni BIM"
        )

@router.get("/{model_id}/metadata", response_model=BIMMetadataResponse)
async def get_bim_model_metadata(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene i metadati di un modello BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Se il modello non ha metadati, prova a parsare
        if not model.has_metadata:
            try:
                metadata_result = await bim_parser.parse_bim_file(model)
                
                if metadata_result.get("parsing_success"):
                    # Aggiorna modello con metadati estratti
                    for key, value in metadata_result.items():
                        if hasattr(model, key) and key not in ["extracted_at", "parsing_success", "parsing_message"]:
                            setattr(model, key, value)
                    
                    session.commit()
                    session.refresh(model)
                    
                    return BIMMetadataResponse(
                        model_id=model.id,
                        **{k: v for k, v in metadata_result.items() if k not in ["extracted_at", "parsing_success", "parsing_message"]},
                        extracted_at=metadata_result.get("extracted_at", datetime.now(timezone.utc)),
                        parsing_success=True,
                        parsing_message=metadata_result.get("parsing_message", "Parsing completato")
                    )
                else:
                    return BIMMetadataResponse(
                        model_id=model.id,
                        extracted_at=datetime.now(timezone.utc),
                        parsing_success=False,
                        parsing_message=metadata_result.get("parsing_message", "Parsing fallito")
                    )
            except Exception as e:
                logger.error(f"Errore parsing metadati: {e}")
                return BIMMetadataResponse(
                    model_id=model.id,
                    extracted_at=datetime.now(timezone.utc),
                    parsing_success=False,
                    parsing_message=f"Errore parsing: {str(e)}"
                )
        
        # Restituisce metadati esistenti
        return BIMMetadataResponse(
            model_id=model.id,
            total_area=model.total_area,
            total_volume=model.total_volume,
            floor_count=model.floor_count,
            room_count=model.room_count,
            building_height=model.building_height,
            project_author=model.project_author,
            project_organization=model.project_organization,
            project_phase=model.project_phase,
            coordinate_system=model.coordinate_system,
            units=model.units,
            extracted_at=model.updated_at,
            parsing_success=True,
            parsing_message="Metadati già estratti"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BIM] Errore durante recupero metadati BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei metadati BIM"
        )

@router.get("/{model_id}/download")
async def download_bim_model(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Scarica un modello BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Ottieni il modello dal database
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Scarica il file da MinIO
        minio_service = get_minio_service()
        file_data = minio_service.download_file(
            storage_path=model.file_url,
            tenant_id=tenant_id
        )
        
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File non trovato nello storage"
            )
        
        # Crea response di streaming
        import io
        from fastapi.responses import StreamingResponse
        
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
        print(f"[BIM] Errore durante download modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il download del modello BIM"
        )

@router.put("/{model_id}", response_model=BIMModelResponse)
async def update_bim_model(
    model_id: int,
    model_update: dict,
    current_user: User = Depends(require_permission_in_tenant("write_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un modello BIM del tenant corrente.
    Richiede permesso 'write_bim_models' nel tenant attivo.
    """
    try:
        # Ottieni il modello dal database
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Aggiorna i campi del modello
        for field, value in model_update.items():
            if hasattr(model, field):
                setattr(model, field, value)
        
        session.add(model)
        session.commit()
        session.refresh(model)
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante aggiornamento modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento del modello BIM"
        )

@router.delete("/{model_id}")
async def delete_bim_model(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("delete_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Elimina un modello BIM del tenant corrente.
    Richiede permesso 'delete_bim_models' nel tenant attivo.
    """
    try:
        # Ottieni il modello dal database
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Elimina il file da MinIO
        minio_service = get_minio_service()
        minio_service.delete_file(
            storage_path=model.file_url,
            tenant_id=tenant_id
        )
        
        # Elimina il record dal database
        session.delete(model)
        session.commit()
        
        return {"message": "Modello BIM eliminato con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante eliminazione modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'eliminazione del modello BIM"
        )

# Endpoint per conversione asincrona con supporto multi-tenant

@router.post("/convert", response_model=BIMConversionResponse)
async def convert_bim_model(
    request: BIMConversionRequest,
    current_user: User = Depends(require_permission_in_tenant("write_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Avvia la conversione asincrona di un modello BIM del tenant corrente.
    Richiede permesso 'write_bim_models' nel tenant attivo.
    """
    try:
        # Verifica che il modello esista e appartenga al tenant
        query = select(BIMModel).where(
            BIMModel.id == request.model_id,
            BIMModel.tenant_id == tenant_id
        )
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Avvia conversione asincrona
        result = process_bim_model.delay(request.model_id, request.conversion_type)
        
        # Aggiorna stato del modello
        model.conversion_status = "processing"
        model.conversion_message = "Conversione avviata"
        model.conversion_started_at = datetime.now(timezone.utc)
        session.commit()
        
        return BIMConversionResponse(
            success=True,
            model_id=request.model_id,
            conversion_type=request.conversion_type,
            task_id=result.id,
            message="Conversione avviata con successo",
            estimated_duration=300 if request.conversion_type == "rvt_to_ifc" else 120
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante avvio conversione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'avvio della conversione"
        )

@router.get("/convert/{model_id}/status", response_model=BIMConversionStatusResponse)
async def get_bim_conversion_status(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene lo stato di conversione di un modello BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Verifica che il modello esista e appartenga al tenant
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Ottieni stato conversione
        status_info = get_conversion_status(model_id)
        
        return BIMConversionStatusResponse(
            model_id=model_id,
            conversion_status=model.conversion_status,
            conversion_message=model.conversion_message,
            conversion_progress=model.conversion_progress or 0,
            conversion_started_at=model.conversion_started_at,
            conversion_completed_at=model.conversion_completed_at,
            converted_file_url=model.converted_file_url,
            validation_report_url=model.validation_report_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante recupero stato conversione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dello stato di conversione"
        )

@router.post("/convert/batch", response_model=BIMBatchConversionResponse)
async def batch_convert_bim_models(
    request: BIMBatchConversionRequest,
    current_user: User = Depends(require_permission_in_tenant("write_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Avvia la conversione batch di modelli BIM del tenant corrente.
    Richiede permesso 'write_bim_models' nel tenant attivo.
    """
    try:
        # Verifica che tutti i modelli esistano e appartengano al tenant
        query = select(BIMModel).where(
            BIMModel.id.in_(request.model_ids),
            BIMModel.tenant_id == tenant_id
        )
        models = safe_exec(session, query).all()
        
        if len(models) != len(request.model_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alcuni modelli BIM non trovati"
            )
        
        # Avvia conversione batch
        result = batch_convert_models.delay(request.model_ids, request.conversion_type)
        
        # Aggiorna stato dei modelli
        for model in models:
            model.conversion_status = "processing"
            model.conversion_message = "Conversione batch avviata"
            model.conversion_started_at = datetime.now(timezone.utc)
        
        session.commit()
        
        return BIMBatchConversionResponse(
            success=True,
            model_ids=request.model_ids,
            conversion_type=request.conversion_type,
            task_id=result.id,
            message=f"Conversione batch avviata per {len(models)} modelli",
            estimated_duration=len(models) * 120
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante avvio conversione batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'avvio della conversione batch"
        )

@router.get("/convert/status", response_model=List[BIMConversionStatusResponse])
async def get_all_conversion_status(
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene lo stato di conversione di tutti i modelli BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Query per modelli del tenant con conversione in corso
        query = select(BIMModel).where(
            BIMModel.tenant_id == tenant_id,
            BIMModel.conversion_status.in_(["pending", "processing", "validating"])
        )
        
        models = safe_exec(session, query).all()
        
        status_list = []
        for model in models:
            status_list.append(BIMConversionStatusResponse(
                model_id=model.id,
                conversion_status=model.conversion_status,
                conversion_message=model.conversion_message,
                conversion_progress=model.conversion_progress or 0,
                conversion_started_at=model.conversion_started_at,
                conversion_completed_at=model.conversion_completed_at,
                converted_file_url=model.converted_file_url,
                validation_report_url=model.validation_report_url
            ))
        
        return status_list
        
    except Exception as e:
        print(f"[BIM] Errore durante recupero stati conversione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero degli stati di conversione"
        )

@router.delete("/convert/{model_id}/cancel")
async def cancel_bim_conversion(
    model_id: int,
    current_user: User = Depends(require_permission_in_tenant("write_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Cancella la conversione di un modello BIM del tenant corrente.
    Richiede permesso 'write_bim_models' nel tenant attivo.
    """
    try:
        # Verifica che il modello esista e appartenga al tenant
        query = select(BIMModel).where(
            BIMModel.id == model_id,
            BIMModel.tenant_id == tenant_id
        )
        model = safe_exec(session, query).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modello BIM non trovato"
            )
        
        # Aggiorna stato del modello
        model.conversion_status = "cancelled"
        model.conversion_message = "Conversione cancellata dall'utente"
        session.commit()
        
        return {"message": "Conversione cancellata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante cancellazione conversione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la cancellazione della conversione"
        )

@router.get("/storage/info")
async def get_bim_storage_info(
    current_user: User = Depends(require_permission_in_tenant("read_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene informazioni sullo storage BIM del tenant corrente.
    Richiede permesso 'read_bim_models' nel tenant attivo.
    """
    try:
        # Lista i file nella cartella bim del tenant
        minio_service = get_minio_service()
        files = minio_service.list_files(
            folder="bim",
            tenant_id=tenant_id
        )
        
        # Calcola statistiche
        total_files = len(files)
        total_size = sum(file["file_size"] for file in files)
        
        # Statistiche per formato
        format_stats = {}
        for file in files:
            filename = file["filename"]
            ext = os.path.splitext(filename)[1].lower()
            if ext not in format_stats:
                format_stats[ext] = {"count": 0, "size": 0}
            format_stats[ext]["count"] += 1
            format_stats[ext]["size"] += file["file_size"]
        
        return {
            "tenant_id": str(tenant_id),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "format_stats": format_stats,
            "files": files
        }
        
    except Exception as e:
        print(f"[BIM] Errore durante recupero info storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle informazioni dello storage"
        )

# TODO: Implementare endpoint per preview modelli BIM
# TODO: Aggiungere endpoint per condivisione modelli tra utenti dello stesso tenant
# TODO: Implementare versioning dei modelli BIM
# TODO: Aggiungere endpoint per export modelli in formati diversi 