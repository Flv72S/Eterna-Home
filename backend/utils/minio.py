from fastapi import UploadFile
import os
import logging
import traceback
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from config.cloud_config import settings
import io

logger = logging.getLogger(__name__)
UPLOAD_DIR = "uploads"

# Assicurati che la directory esista
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_minio_client() -> Minio:
    """
    Crea e restituisce un client MinIO configurato.
    """
    try:
        logger.debug(f"Tentativo di connessione a MinIO su {settings.MINIO_ENDPOINT}")
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Verifica che il bucket esista
        if not client.bucket_exists(settings.MINIO_BUCKET_LEGACY):
            logger.debug(f"Bucket {settings.MINIO_BUCKET_LEGACY} non trovato, creazione in corso...")
            client.make_bucket(settings.MINIO_BUCKET_LEGACY)
            logger.debug(f"Bucket {settings.MINIO_BUCKET_LEGACY} creato con successo")
        
        logger.debug("Connessione a MinIO stabilita con successo")
        return client
    except S3Error as e:
        error_msg = f"Errore S3 durante la connessione a MinIO: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Errore durante la connessione a MinIO: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise

async def upload_file_to_minio(
    minio_client: Minio,
    bucket_name: str,
    object_name: str,
    file_content: bytes,
    content_type: str
) -> str:
    """
    Carica un file su MinIO e restituisce l'URL del file.
    """
    try:
        logger.debug(f"Caricamento file {object_name} su MinIO...")
        logger.debug(f"type(file_content): {type(file_content)}")
        logger.debug(f"file_content has 'read': {hasattr(file_content, 'read')}")
        
        # Gestione robusta del tipo di file_content e della dimensione
        if hasattr(file_content, 'read'):
            logger.debug("file_content è già un file-like object")
            file_content.seek(0, 2)  # Vai alla fine
            size = file_content.tell()
            file_content.seek(0)     # Torna all'inizio
            data_stream = file_content
        else:
            logger.debug("file_content è bytes, creo BytesIO")
            size = len(file_content)
            data_stream = io.BytesIO(file_content)
        
        logger.debug(f"type(data_stream): {type(data_stream)}")
        logger.debug(f"data_stream has 'read': {hasattr(data_stream, 'read')}")
        logger.debug(f"size: {size}")
        
        minio_client.put_object(
            bucket_name,
            object_name,
            data_stream,
            size,
            content_type=content_type
        )
        logger.debug(f"File {object_name} caricato con successo")
        
        # Genera l'URL permanente del file
        file_url = f"{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"
        logger.debug(f"URL generato: {file_url}")
        
        return file_url
    except S3Error as e:
        error_msg = f"Errore S3 durante il caricamento del file su MinIO: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Errore durante il caricamento del file su MinIO: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise

async def upload_file(file: UploadFile) -> str:
    """
    Carica un file su MinIO e restituisce l'URL del file.
    """
    try:
        # Genera un nome file unico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        
        # Leggi il contenuto del file
        content = await file.read()
        
        # Carica su MinIO
        minio_client = get_minio_client()
        file_url = await upload_file_to_minio(
            minio_client,
            settings.MINIO_BUCKET_LEGACY,
            filename,
            content,
            file.content_type
        )
        
        return file_url
    except Exception as e:
        error_msg = f"Errore durante il caricamento del file: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise

def get_file_url(file_path: str) -> str:
    """
    Restituisce l'URL per accedere al file su MinIO.
    """
    if not file_path:
        return None
    return file_path  # Il file_path è già l'URL completo di MinIO 