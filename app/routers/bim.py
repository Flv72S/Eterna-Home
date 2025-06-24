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
    require_permission_in_tenant,
    get_session
)
from app.models.user import User
from app.models.bim_model import BIMModel
from app.schemas.bim import (
    BIMModelCreate, BIMModelResponse, BIMModelListResponse,
    BIMConversionRequest, BIMConversionResponse, BIMConversionStatusResponse,
    BIMBatchConversionRequest, BIMBatchConversionResponse
)
from app.services.minio_service import get_minio_service
from app.workers.conversion_worker import process_bim_model, batch_convert_models, get_conversion_status
from app.db.utils import safe_exec

router = APIRouter(prefix="/api/v1/bim", tags=["BIM Models"])

@router.post("/upload", response_model=BIMModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_bim_model(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    current_user: User = Depends(require_permission_in_tenant("write_bim_models")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Carica un modello BIM nel tenant corrente.
    Richiede permesso 'write_bim_models' nel tenant attivo.
    """
    try:
        # Validazione file
        allowed_extensions = ['.ifc', '.rvt', '.dwg', '.dxf', '.skp', '.pln']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato file non supportato. Formati consentiti: {', '.join(allowed_extensions)}"
            )
        
        # Validazione dimensione (max 100MB)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File troppo grande. Dimensione massima: 100MB"
            )
        
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
            name=name or file.filename,
            description=description,
            format=file_extension[1:],
            file_url=upload_result["storage_path"],
            file_size=len(content),
            checksum=checksum,
            user_id=current_user.id,
            tenant_id=tenant_id
        )
        
        bim_model = BIMModel(**bim_model_data.dict())
        session.add(bim_model)
        session.commit()
        session.refresh(bim_model)
        
        return bim_model
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BIM] Errore durante upload modello BIM: {e}")
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
        print(f"[BIM] Errore durante listaggio modelli BIM: {e}")
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
        print(f"[BIM] Errore durante recupero modello BIM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del modello BIM"
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