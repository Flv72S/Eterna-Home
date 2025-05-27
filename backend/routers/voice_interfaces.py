from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from backend.db.session import get_db
from backend.models.user import User
from backend.utils.auth import get_current_user
from backend.config.cloud_config import settings
from backend.utils.minio import get_minio_client, upload_file_to_minio
from datetime import datetime

router = APIRouter(
    prefix="/voice-interfaces",
    tags=["Voice Interfaces"]
)

@router.post("/command")
async def process_voice_command(
    command_text: str = Form(...),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Simulazione dell'elaborazione del comando
        response_text = f"Comando ricevuto: {command_text}. Elaborazione simulata."
        
        # Se è stato fornito un file audio, lo carica su MinIO
        if audio_file:
            content = await audio_file.read()
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{audio_file.filename}"
            minio_client = get_minio_client()
            file_url = await upload_file_to_minio(
                minio_client,
                settings.MINIO_BUCKET_AUDIO,
                filename,
                content,
                audio_file.content_type or "audio/wav"
            )
            response_text += f" File audio caricato: {file_url}"
        
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 