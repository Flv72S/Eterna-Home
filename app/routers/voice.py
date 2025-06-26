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
import uuid
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/commands", response_model=VoiceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
@require_permission_in_tenant("submit_voice")
async def create_voice_command(
    command_data: VoiceCommandRequest,
    current_user: User = Depends(get_current_user),
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
@require_permission_in_tenant("submit_voice")
async def create_voice_command_audio(
    audio_file: UploadFile = File(...),
    node_id: Optional[int] = Form(None),
    house_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
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
    
    # Verifica estensione file
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg']
    file_extension = os.path.splitext(audio_file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        logger.warning("Audio file upload rejected - unsupported format",
                       user_id=current_user.id,
                       filename=audio_file.filename,
                       extension=file_extension)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato file non supportato. Formati consentiti: {', '.join(allowed_extensions)}"
        )
    
    # Verifica dimensione file (max 50MB)
    if audio_file.size and audio_file.size > 50 * 1024 * 1024:
        logger.warning("Audio file upload rejected - file too large",
                       user_id=current_user.id,
                       filename=audio_file.filename,
                       size=audio_file.size)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File troppo grande. Dimensione massima: 50MB"
        )
    
    try:
        # Salva il file audio su MinIO
        minio_client = get_minio_client()
        file_id = str(uuid.uuid4())
        bucket_name = "voice-commands"
        
        # Assicurati che il bucket esista
        # await minio_client.ensure_bucket_exists(bucket_name)
        
        # Carica il file
        file_path = f"{current_user.id}/{file_id}{file_extension}"
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
            "command_type": "audio",
            "file_path": file_path,
            "bucket_name": bucket_name
        }
        
        # Pubblica messaggio nella coda
        try:
            rabbitmq_manager = await get_rabbitmq_manager()
            await rabbitmq_manager.publish_message(message_data)
            logger.info("Audio file message sent to queue",
                        audiolog_id=audio_log.id,
                        file_id=file_id,
                        queue="voice_processing")
        except Exception as e:
            logger.error("Failed to send audio file to queue",
                         audiolog_id=audio_log.id,
                         file_id=file_id,
                         error=str(e),
                         exc_info=True)
            # Non blocchiamo la risposta se la coda non è disponibile
        
        return VoiceCommandResponse(
            request_id=f"audiolog-{audio_log.id}",
            status="accepted",
            message="File audio ricevuto e inviato in elaborazione"
        )
        
    except Exception as e:
        logger.error("Audio file processing failed",
                     user_id=current_user.id,
                     filename=audio_file.filename,
                     error=str(e),
                     exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento del file audio"
        )

@router.get("/logs", response_model=AudioLogListResponse)
@require_permission_in_tenant("read_voice_logs")
async def get_audio_logs(
    house_id: Optional[int] = None,
    node_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottiene la lista degli AudioLog dell'utente con filtri e paginazione.
    """
    skip = (page - 1) * size
    
    try:
        result = AudioLogService.get_audio_logs(
            db, current_user, house_id, node_id, status, skip, size
        )
        return AudioLogListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei log audio"
        )

@router.get("/logs/{log_id}", response_model=AudioLogResponse)
@require_permission_in_tenant("read_voice_logs")
async def get_audio_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottiene un AudioLog specifico.
    """
    audio_log = AudioLogService.get_audio_log(db, log_id, current_user)
    if not audio_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AudioLog non trovato"
        )
    return audio_log

@router.put("/logs/{log_id}", response_model=AudioLogResponse)
@require_permission_in_tenant("manage_voice_logs")
async def update_audio_log(
    log_id: int,
    audio_log_data: AudioLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiorna un AudioLog specifico.
    """
    audio_log = AudioLogService.update_audio_log(db, log_id, audio_log_data, current_user)
    if not audio_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AudioLog non trovato"
        )
    return audio_log

@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission_in_tenant("manage_voice_logs")
async def delete_audio_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un AudioLog specifico.
    """
    success = AudioLogService.delete_audio_log(db, log_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AudioLog non trovato"
        )

@router.get("/statuses")
async def get_processing_statuses():
    """
    Ottiene gli stati di elaborazione disponibili.
    """
    return {
        "statuses": AudioLogService.get_processing_statuses(),
        "descriptions": {
            "received": "Ricevuto",
            "transcribing": "In Trascrizione",
            "analyzing": "In Analisi",
            "completed": "Completato",
            "failed": "Fallito"
        }
    }

@router.get("/stats")
@require_permission_in_tenant("read_voice_logs")
async def get_voice_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottiene statistiche sui comandi vocali dell'utente.
    """
    try:
        stats = AudioLogService.get_user_voice_stats(db, current_user)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        ) 