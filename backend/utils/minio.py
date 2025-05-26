from fastapi import UploadFile
import os
from datetime import datetime
from minio import Minio
from config.cloud_config import settings

UPLOAD_DIR = "uploads"

# Assicurati che la directory esista
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_minio_client() -> Minio:
    """
    Crea e restituisce un client MinIO configurato.
    """
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )

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
    # Assicurati che il bucket esista
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    # Carica il file
    minio_client.put_object(
        bucket_name,
        object_name,
        file_content,
        len(file_content),
        content_type=content_type
    )
    
    # Genera l'URL del file
    return f"{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"

async def upload_file(file: UploadFile) -> str:
    """
    Carica un file su MinIO e restituisce l'URL del file.
    """
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

def get_file_url(file_path: str) -> str:
    """
    Restituisce l'URL per accedere al file su MinIO.
    """
    if not file_path:
        return None
    return file_path  # Il file_path è già l'URL completo di MinIO 