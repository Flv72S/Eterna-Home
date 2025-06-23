from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlmodel import Session
from app.core.deps import get_current_user, get_db
from app.models import User, BIMModel
from app.schemas.bim import (
    BIMModelCreate, BIMModelResponse, BIMModelListResponse,
    BIMConversionRequest, BIMConversionResponse, BIMConversionStatusResponse,
    BIMBatchConversionRequest, BIMBatchConversionResponse
)
from app.services.minio_service import MinioService
from app.workers.conversion_worker import process_bim_model, batch_convert_models, get_conversion_status
import hashlib
import os
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/bim", tags=["BIM Models"])

@router.post("/upload", response_model=BIMModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_bim_model(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Carica un modello BIM."""
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
    
    try:
        # Calcola checksum
        content = await file.read()
        checksum = hashlib.sha256(content).hexdigest()
        
        # Carica su MinIO
        minio_service = MinioService()
        bucket_name = "bim"
        file_path = f"{current_user.id}/{checksum[:8]}_{file.filename}"
        
        await minio_service.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file_data=content,
            content_type=file.content_type
        )
        
        # Crea record nel database
        bim_model_data = BIMModelCreate(
            name=name or file.filename,
            description=description,
            format=file_extension[1:],
            file_url=f"{bucket_name}/{file_path}",
            file_size=len(content),
            checksum=checksum,
            user_id=current_user.id
        )
        
        bim_model = BIMModel(**bim_model_data.dict())
        db.add(bim_model)
        db.commit()
        db.refresh(bim_model)
        
        return bim_model
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il caricamento: {str(e)}"
        )

@router.get("/", response_model=BIMModelListResponse)
async def get_bim_models(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene la lista dei modelli BIM dell'utente."""
    from sqlmodel import select, func
    
    # Query per contare totale
    total_query = select(func.count(BIMModel.id)).where(BIMModel.user_id == current_user.id)
    total = db.exec(total_query).first()
    
    # Query per lista
    query = (
        select(BIMModel)
        .where(BIMModel.user_id == current_user.id)
        .order_by(BIMModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    models = db.exec(query).all()
    
    return {
        "items": models,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/{model_id}", response_model=BIMModelResponse)
async def get_bim_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene un modello BIM specifico."""
    from sqlmodel import select
    
    query = select(BIMModel).where(
        BIMModel.id == model_id,
        BIMModel.user_id == current_user.id
    )
    model = db.exec(query).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modello BIM non trovato"
        )
    
    return model

# Nuovi endpoint per conversione asincrona

@router.post("/convert", response_model=BIMConversionResponse)
async def convert_bim_model(
    request: BIMConversionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Avvia la conversione asincrona di un modello BIM."""
    from sqlmodel import select
    
    # Verifica che il modello esista e appartenga all'utente
    query = select(BIMModel).where(
        BIMModel.id == request.model_id,
        BIMModel.user_id == current_user.id
    )
    model = db.exec(query).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modello BIM non trovato"
        )
    
    try:
        # Avvia conversione asincrona
        result = process_bim_model.delay(request.model_id, request.conversion_type)
        
        # Aggiorna stato del modello
        model.conversion_status = "processing"
        model.conversion_message = "Conversione avviata"
        model.conversion_started_at = datetime.now(timezone.utc)
        db.commit()
        
        return BIMConversionResponse(
            success=True,
            model_id=request.model_id,
            conversion_type=request.conversion_type,
            task_id=result.id,
            message="Conversione avviata con successo",
            estimated_duration=300 if request.conversion_type == "rvt_to_ifc" else 120
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'avvio della conversione: {str(e)}"
        )

@router.get("/convert/{model_id}/status", response_model=BIMConversionStatusResponse)
async def get_bim_conversion_status(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene lo stato di conversione di un modello BIM."""
    from sqlmodel import select
    
    # Verifica che il modello esista e appartenga all'utente
    query = select(BIMModel).where(
        BIMModel.id == model_id,
        BIMModel.user_id == current_user.id
    )
    model = db.exec(query).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modello BIM non trovato"
        )
    
    return BIMConversionStatusResponse(
        model_id=model.id,
        status=model.conversion_status,
        message=model.conversion_message,
        progress=model.conversion_progress,
        converted_file_url=model.converted_file_url,
        validation_report_url=model.validation_report_url,
        conversion_duration=model.conversion_duration,
        updated_at=model.updated_at
    )

@router.post("/convert/batch", response_model=BIMBatchConversionResponse)
async def batch_convert_bim_models(
    request: BIMBatchConversionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Avvia la conversione asincrona di più modelli BIM."""
    from sqlmodel import select
    
    # Verifica che tutti i modelli esistano e appartengano all'utente
    query = select(BIMModel).where(
        BIMModel.id.in_(request.model_ids),
        BIMModel.user_id == current_user.id
    )
    models = db.exec(query).all()
    
    if len(models) != len(request.model_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alcuni modelli BIM non trovati o non accessibili"
        )
    
    try:
        # Avvia conversione batch asincrona
        result = batch_convert_models.delay(request.model_ids, request.conversion_type)
        
        return BIMBatchConversionResponse(
            success=True,
            total_models=len(request.model_ids),
            successful=0,
            failed=0,
            task_ids=[result.id],
            message=f"Conversione batch avviata per {len(request.model_ids)} modelli"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'avvio della conversione batch: {str(e)}"
        )

@router.get("/convert/status", response_model=List[BIMConversionStatusResponse])
async def get_all_conversion_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene lo stato di conversione di tutti i modelli BIM dell'utente."""
    from sqlmodel import select
    
    query = select(BIMModel).where(
        BIMModel.user_id == current_user.id,
        BIMModel.conversion_status.in_(["processing", "validating", "completed", "failed"])
    )
    models = db.exec(query).all()
    
    return [
        BIMConversionStatusResponse(
            model_id=model.id,
            status=model.conversion_status,
            message=model.conversion_message,
            progress=model.conversion_progress,
            converted_file_url=model.converted_file_url,
            validation_report_url=model.validation_report_url,
            conversion_duration=model.conversion_duration,
            updated_at=model.updated_at
        )
        for model in models
    ]

@router.delete("/convert/{model_id}/cancel")
async def cancel_bim_conversion(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancella la conversione di un modello BIM."""
    from sqlmodel import select
    
    # Verifica che il modello esista e appartenga all'utente
    query = select(BIMModel).where(
        BIMModel.id == model_id,
        BIMModel.user_id == current_user.id
    )
    model = db.exec(query).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modello BIM non trovato"
        )
    
    if model.conversion_status not in ["processing", "validating"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile cancellare una conversione non in corso"
        )
    
    try:
        # Aggiorna stato del modello
        model.conversion_status = "cancelled"
        model.conversion_message = "Conversione cancellata dall'utente"
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return {"success": True, "message": "Conversione cancellata con successo"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la cancellazione: {str(e)}"
        ) 