from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session
from app.core.deps import get_current_user, get_db
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
from app.core.storage.minio import MinioService
import uuid
import os

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/commands", response_model=VoiceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
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
    try:
        audio_log = AudioLogService.process_voice_command(db, command_data, current_user)
        
        return VoiceCommandResponse(
            request_id=f"audiolog-{audio_log.id}",
            status="accepted",
            message="Comando vocale ricevuto e inviato in elaborazione"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.post("/commands/audio", response_model=VoiceCommandResponse, status_code=status.HTTP_202_ACCEPTED)
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
    # Verifica estensione file
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg']
    file_extension = os.path.splitext(audio_file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato file non supportato. Formati consentiti: {', '.join(allowed_extensions)}"
        )
    
    # Verifica dimensione file (max 50MB)
    if audio_file.size and audio_file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File troppo grande. Dimensione massima: 50MB"
        )
    
    try:
        # Salva il file audio su MinIO
        minio_service = MinioService()
        file_id = str(uuid.uuid4())
        bucket_name = "voice-commands"
        
        # Assicurati che il bucket esista
        await minio_service.ensure_bucket_exists(bucket_name)
        
        # Carica il file
        file_path = f"{current_user.id}/{file_id}{file_extension}"
        await minio_service.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file_data=audio_file.file,
            content_type=audio_file.content_type
        )
        
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
        
        # TODO: In futuro, qui si invierà il messaggio alla coda per trascrizione audio
        # await send_audio_to_queue(audio_log.id, file_path)
        
        return VoiceCommandResponse(
            request_id=f"audiolog-{audio_log.id}",
            status="accepted",
            message="File audio ricevuto e inviato in elaborazione"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il caricamento del file audio"
        )

@router.get("/logs", response_model=AudioLogListResponse)
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