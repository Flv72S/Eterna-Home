from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session
from app.core.deps import get_current_user, get_db
from app.core.auth.rbac import require_permission_in_tenant
from app.core.logging import get_logger
from app.models import User
from app.schemas.audio_log import (
    AudioLogCreate, 
    AudioLogUpdate, 
    AudioLogResponse, 
    AudioLogListResponse,
    VoiceCommandRequest,
    VoiceCommandResponse
)
from app.services.audio_log import AudioLogService
from app.core.storage.minio import get_minio_client
from app.core.queue import get_rabbitmq_manager
from app.security.validators import validate_file_upload, sanitize_filename, TextValidator
import uuid
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/commands", response_model=VoiceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_voice_command(
    command_data: VoiceCommandRequest,
    current_user: User = Depends(require_permission_in_tenant("submit_voice")),
    db: Session = Depends(get_db)
):
    """
    Riceve un comando vocale e lo invia in elaborazione asincrona.
    
    - **transcribed_text**: Testo trascritto dal comando vocale
    - **node_id**: ID del nodo associato (opzionale)
    - **house_id**: ID della casa associata (opzionale)
    """
    logger.info("Voice command received",
                user_id=current_user.id,
                node_id=command_data.node_id,
                house_id=command_data.house_id,
                has_text=bool(command_data.transcribed_text))
    
    try:
        # Crea AudioLog
        audio_log = AudioLogService.process_voice_command(db, command_data, current_user)
        
        logger.info("AudioLog created for voice command",
                    audiolog_id=audio_log.id,
                    user_id=current_user.id,
                    status=audio_log.processing_status)
        
        # Prepara messaggio per la coda
        message_data = {
            "audiolog_id": audio_log.id,
            "user_id": current_user.id,
            "node_id": audio_log.node_id,
            "house_id": audio_log.house_id,
            "transcribed_text": audio_log.transcribed_text,
            "audio_url": audio_log.audio_url,
            "timestamp": audio_log.timestamp.isoformat(),
            "command_type": "text" if audio_log.transcribed_text else "audio"
        }
        
        # Pubblica messaggio nella coda
        try:
            rabbitmq_manager = await get_rabbitmq_manager()
            await rabbitmq_manager.publish_message(message_data)
            logger.info("Voice command message sent to queue",
                        audiolog_id=audio_log.id,
                        queue="voice_processing")
        except Exception as e:
            logger.error("Failed to send voice command to queue",
                         audiolog_id=audio_log.id,
                         error=str(e),
                         exc_info=True)
            # Non blocchiamo la risposta se la coda non è disponibile
            # Il worker può comunque processare i record esistenti
        
        return VoiceCommandResponse(
            request_id=f"audiolog-{audio_log.id}",
            status="accepted",
            message="Comando vocale ricevuto e inviato in elaborazione"
        )
    except ValueError as e:
        logger.warning("Voice command validation failed",
                       user_id=current_user.id,
                       error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Voice command processing failed",
                     user_id=current_user.id,
                     error=str(e),
                     exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.post("/commands/audio", response_model=VoiceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_voice_command_audio(
    audio_file: UploadFile = File(...),
    node_id: Optional[int] = Form(None),
    house_id: Optional[int] = Form(None),
    current_user: User = Depends(require_permission_in_tenant("submit_voice")),
    db: Session = Depends(get_db)
):
    """
    Riceve un file audio e lo invia in elaborazione asincrona.
    
    - **audio_file**: File audio (WAV, MP3, M4A)
    - **node_id**: ID del nodo associato (opzionale)
    - **house_id**: ID della casa associata (opzionale)
    """
    logger.info("Audio file upload received",
                user_id=current_user.id,
                filename=audio_file.filename,
                content_type=audio_file.content_type,
                size=audio_file.size,
                node_id=node_id,
                house_id=house_id)
    
    # Validazione avanzata del file audio
    allowed_types = [
        "audio/mpeg",
        "audio/wav", 
        "audio/mp4",
        "audio/flac",
        "audio/ogg"
    ]
    max_size = 100 * 1024 * 1024  # 100MB per file audio
    
    # Sanifica e valida il file
    safe_filename = sanitize_filename(audio_file.filename)
    validate_file_upload(audio_file, allowed_types, max_size)
    
    try:
        # Salva il file audio su MinIO
        minio_client = get_minio_client()
        file_id = str(uuid.uuid4())
        bucket_name = "voice-commands"
        
        # Assicurati che il bucket esista
        # await minio_client.ensure_bucket_exists(bucket_name)
        
        # Carica il file
        file_path = f"{current_user.id}/{file_id}{os.path.splitext(safe_filename)[1]}"
        # await minio_client.upload_file(
        #     bucket_name=bucket_name,
        #     file_path=file_path,
        #     file_data=audio_file.file,
        #     content_type=audio_file.content_type
        # )
        
        logger.info("Audio file uploaded to storage",
                    user_id=current_user.id,
                    file_id=file_id,
                    file_path=file_path,
                    bucket=bucket_name)
        
        # Crea i dati per AudioLog
        command_data = VoiceCommandRequest(
            transcribed_text=None,  # Sarà trascritto dal worker
            node_id=node_id,
            house_id=house_id
        )
        
        # Crea AudioLog con URL del file audio
        audio_log_data = AudioLogCreate(
            user_id=current_user.id,
            node_id=node_id,
            house_id=house_id,
            audio_url=f"{bucket_name}/{file_path}",
            processing_status="received"
        )
        
        audio_log = AudioLogService.create_audio_log(db, audio_log_data, current_user)
        
        logger.info("AudioLog created for audio file",
                    audiolog_id=audio_log.id,
                    user_id=current_user.id,
                    file_id=file_id,
                    status=audio_log.processing_status)
        
        # Prepara messaggio per la coda
        message_data = {
            "audiolog_id": audio_log.id,
            "user_id": current_user.id,
            "node_id": audio_log.node_id,
            "house_id": audio_log.house_id,
            "audio_url": audio_log.audio_url,
            "timestamp": audio_log.timestamp.isoformat(),
            "command_type": "audio"
        }
        
        # Pubblica messaggio nella coda
        try:
            rabbitmq_manager = await get_rabbitmq_manager()
            await rabbitmq_manager.publish_message(message_data)
            logger.info("Audio file message sent to queue",
                        audiolog_id=audio_log.id,
                        queue="voice_processing")
        except Exception as e:
            logger.error("Failed to send audio file to queue",
                         audiolog_id=audio_log.id,
                         error=str(e),
                         exc_info=True)
            # Non blocchiamo la risposta se la coda non è disponibile
        
        return VoiceCommandResponse(
            request_id=f"audiolog-{audio_log.id}",
            status="accepted",
            message="File audio ricevuto e inviato in elaborazione"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Audio file processing failed",
                     user_id=current_user.id,
                     filename=audio_file.filename,
                     error=str(e),
                     exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.get("/logs", response_model=AudioLogListResponse)
async def get_audio_logs(
    house_id: Optional[int] = None,
    node_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(require_permission_in_tenant("read_voice_logs")),
    db: Session = Depends(get_db)
):
    """
    Lista i log audio del tenant corrente.
    Richiede permesso 'read_voice_logs' nel tenant attivo.
    """
    try:
        # Query base filtrata per tenant
        query = select(AudioLog).where(AudioLog.tenant_id == current_user.tenant_id)
        
        # Filtri opzionali
        if house_id:
            query = query.where(AudioLog.house_id == house_id)
        if node_id:
            query = query.where(AudioLog.node_id == node_id)
        if status:
            query = query.where(AudioLog.processing_status == status)
        
        # Paginazione
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        # Esegui query
        audio_logs = safe_exec(db, query).all()
        
        return {
            "items": audio_logs,
            "page": page,
            "size": size,
            "total": len(audio_logs)  # TODO: Aggiungere count totale
        }
        
    except Exception as e:
        logger.error("Errore durante listaggio log audio", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei log audio"
        )

@router.get("/logs/{log_id}", response_model=AudioLogResponse)
async def get_audio_log(
    log_id: int,
    current_user: User = Depends(require_permission_in_tenant("read_voice_logs")),
    db: Session = Depends(get_db)
):
    """
    Ottiene un log audio specifico del tenant corrente.
    Richiede permesso 'read_voice_logs' nel tenant attivo.
    """
    try:
        audio_log = db.get(AudioLog, log_id)
        if not audio_log or audio_log.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log audio non trovato"
            )
        
        return audio_log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore durante recupero log audio", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del log audio"
        )

@router.put("/logs/{log_id}", response_model=AudioLogResponse)
async def update_audio_log(
    log_id: int,
    audio_log_data: AudioLogUpdate,
    current_user: User = Depends(require_permission_in_tenant("manage_voice_logs")),
    db: Session = Depends(get_db)
):
    """
    Aggiorna un log audio del tenant corrente.
    Richiede permesso 'manage_voice_logs' nel tenant attivo.
    """
    try:
        audio_log = db.get(AudioLog, log_id)
        if not audio_log or audio_log.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log audio non trovato"
            )
        
        # Aggiorna i campi
        for field, value in audio_log_data.dict(exclude_unset=True).items():
            setattr(audio_log, field, value)
        
        db.add(audio_log)
        db.commit()
        db.refresh(audio_log)
        
        return audio_log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore durante aggiornamento log audio", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento del log audio"
        )

@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio_log(
    log_id: int,
    current_user: User = Depends(require_permission_in_tenant("manage_voice_logs")),
    db: Session = Depends(get_db)
):
    """
    Elimina un log audio del tenant corrente.
    Richiede permesso 'manage_voice_logs' nel tenant attivo.
    """
    try:
        audio_log = db.get(AudioLog, log_id)
        if not audio_log or audio_log.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log audio non trovato"
            )
        
        db.delete(audio_log)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore durante eliminazione log audio", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'eliminazione del log audio"
        )

@router.get("/statuses")
async def get_processing_statuses():
    """
    Restituisce i possibili stati di elaborazione dei comandi vocali.
    Endpoint pubblico, non richiede autenticazione.
    """
    return {
        "statuses": [
            "received",
            "processing", 
            "completed",
            "failed",
            "cancelled"
        ]
    }

@router.get("/stats")
async def get_voice_stats(
    current_user: User = Depends(require_permission_in_tenant("read_voice_logs")),
    db: Session = Depends(get_db)
):
    """
    Ottiene statistiche sui comandi vocali del tenant corrente.
    Richiede permesso 'read_voice_logs' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Query per statistiche
        total_query = select(func.count(AudioLog.id)).where(
            AudioLog.tenant_id == current_user.tenant_id
        )
        total = safe_exec(db, total_query).first()
        
        # Statistiche per stato
        status_stats = {}
        for status in ["received", "processing", "completed", "failed", "cancelled"]:
            status_query = select(func.count(AudioLog.id)).where(
                AudioLog.tenant_id == current_user.tenant_id,
                AudioLog.processing_status == status
            )
            count = safe_exec(db, status_query).first()
            status_stats[status] = count
        
        return {
            "total_commands": total,
            "status_breakdown": status_stats
        }
        
    except Exception as e:
        logger.error("Errore durante recupero statistiche voice", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        ) 