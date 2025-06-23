"""
Router per interfacce locali e integrazione comandi vocali.
Gestisce l'integrazione tra comandi vocali e altre aree del sistema.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session
from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.local_interface import LocalInterfaceService
from app.services.speech_to_text import SpeechToTextService
from app.workers.voice_worker import VoiceWorker
from app.core.config import settings

router = APIRouter(prefix="/api/v1/local-interface", tags=["Local Interface"])

@router.get("/status")
async def get_local_interface_status(
    current_user: User = Depends(get_current_user)
):
    """Ottiene lo stato delle interfacce locali."""
    try:
        local_interface = LocalInterfaceService()
        speech_service = SpeechToTextService()
        
        status_info = {
            "local_interfaces_enabled": settings.ENABLE_LOCAL_INTERFACES,
            "voice_commands_enabled": settings.ENABLE_VOICE_COMMANDS,
            "speech_service_status": speech_service.get_service_status(),
            "integrations": {
                "iot": settings.ENABLE_IOT_INTEGRATION,
                "bim": settings.ENABLE_BIM_INTEGRATION,
                "documents": settings.ENABLE_DOCUMENT_INTEGRATION
            }
        }
        
        return {
            "success": True,
            "status": status_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento stato interfacce: {str(e)}"
        )

@router.post("/voice-command/process")
async def process_voice_command(
    audio_log_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processa un comando vocale tramite interfacce locali."""
    try:
        local_interface = LocalInterfaceService()
        
        # Verifica che l'AudioLog appartenga all'utente
        from app.models.audio_log import AudioLog
        audio_log = db.get(AudioLog, audio_log_id)
        
        if not audio_log or audio_log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AudioLog non trovato o non accessibile"
            )
        
        # Processa comando in background
        background_tasks.add_task(local_interface.process_voice_command, audio_log_id)
        
        return {
            "success": True,
            "message": "Comando vocale avviato per elaborazione",
            "audio_log_id": audio_log_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore elaborazione comando vocale: {str(e)}"
        )

@router.get("/voice-command/status/{audio_log_id}")
async def get_voice_command_status(
    audio_log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene lo stato di elaborazione di un comando vocale."""
    try:
        from app.models.audio_log import AudioLog
        
        audio_log = db.get(AudioLog, audio_log_id)
        
        if not audio_log or audio_log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AudioLog non trovato o non accessibile"
            )
        
        return {
            "success": True,
            "audio_log_id": audio_log_id,
            "status": audio_log.processing_status,
            "transcribed_text": audio_log.transcribed_text,
            "response_text": audio_log.response_text,
            "timestamp": audio_log.timestamp.isoformat() if audio_log.timestamp else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento stato comando: {str(e)}"
        )

@router.get("/speech-to-text/languages")
async def get_supported_languages(
    current_user: User = Depends(get_current_user)
):
    """Ottiene le lingue supportate per la trascrizione audio."""
    try:
        speech_service = SpeechToTextService()
        languages = speech_service.get_supported_languages()
        
        return {
            "success": True,
            "languages": languages,
            "default_language": settings.GOOGLE_SPEECH_LANGUAGE
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento lingue supportate: {str(e)}"
        )

@router.post("/speech-to-text/transcribe")
async def transcribe_audio(
    audio_url: str,
    language_code: str = None,
    current_user: User = Depends(get_current_user)
):
    """Trascrive un file audio usando servizi reali."""
    try:
        if not settings.USE_REAL_SPEECH_TO_TEXT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Servizi di trascrizione audio reali non abilitati"
            )
        
        speech_service = SpeechToTextService()
        
        # Usa lingua di default se non specificata
        if not language_code:
            language_code = settings.GOOGLE_SPEECH_LANGUAGE
        
        result = await speech_service.transcribe_audio(audio_url, language_code)
        
        return {
            "success": True,
            "transcription": result.get("transcription", ""),
            "confidence": result.get("confidence", 0.0),
            "provider": result.get("provider", "unknown"),
            "language_code": result.get("language_code", language_code)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore trascrizione audio: {str(e)}"
        )

@router.get("/worker/status")
async def get_worker_status(
    current_user: User = Depends(get_current_user)
):
    """Ottiene lo stato del worker vocale."""
    try:
        worker = VoiceWorker()
        status_info = await worker.get_worker_status()
        
        return {
            "success": True,
            "worker_status": status_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento stato worker: {str(e)}"
        )

@router.post("/test/voice-command")
async def test_voice_command(
    command_text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Testa un comando vocale simulato."""
    try:
        from app.models.audio_log import AudioLog
        
        # Crea AudioLog di test
        test_audio_log = AudioLog(
            user_id=current_user.id,
            house_id=1,  # Default house
            transcribed_text=command_text,
            processing_status="received"
        )
        
        db.add(test_audio_log)
        db.commit()
        db.refresh(test_audio_log)
        
        # Processa comando
        local_interface = LocalInterfaceService()
        result = await local_interface.process_voice_command(test_audio_log.id)
        
        return {
            "success": True,
            "test_audio_log_id": test_audio_log.id,
            "command_text": command_text,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore test comando vocale: {str(e)}"
        )

@router.get("/integrations/iot/status")
async def get_iot_integration_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene lo stato dell'integrazione IoT."""
    try:
        from app.models.node import Node
        
        # Conta nodi attivi dell'utente
        active_nodes_query = db.exec(
            select(Node).where(
                Node.user_id == current_user.id,
                Node.is_active == True
            )
        ).all()
        
        return {
            "success": True,
            "iot_enabled": settings.ENABLE_IOT_INTEGRATION,
            "active_nodes_count": len(active_nodes_query),
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type,
                    "is_active": node.is_active
                }
                for node in active_nodes_query
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento stato IoT: {str(e)}"
        )

@router.get("/integrations/bim/status")
async def get_bim_integration_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottiene lo stato dell'integrazione BIM."""
    try:
        from app.models.bim_model import BIMModel
        
        # Conta modelli BIM dell'utente
        bim_models_query = db.exec(
            select(BIMModel).where(BIMModel.user_id == current_user.id)
        ).all()
        
        pending_conversions = len([m for m in bim_models_query if m.conversion_status == "pending"])
        completed_conversions = len([m for m in bim_models_query if m.conversion_status == "completed"])
        
        return {
            "success": True,
            "bim_enabled": settings.ENABLE_BIM_INTEGRATION,
            "total_models": len(bim_models_query),
            "pending_conversions": pending_conversions,
            "completed_conversions": completed_conversions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore ottenimento stato BIM: {str(e)}"
        ) 