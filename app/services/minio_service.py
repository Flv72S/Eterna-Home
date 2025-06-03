import os
import uuid
import logging
from datetime import datetime
from typing import Optional, Tuple
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from fastapi import Depends

# Configurazione logger
logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        """Inizializza il client MinIO con le configurazioni dall'ambiente."""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Assicurati che il bucket esista
            if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.client.make_bucket(settings.MINIO_BUCKET_NAME)
            
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Verifica se il bucket esiste e lo crea se necessario."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket {bucket_name}: {str(e)}")
            raise

    def upload_file(self, data: bytes, object_name: str, content_type: str) -> str:
        """Upload a file to MinIO."""
        self.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=data,
            length=len(data),
            content_type=content_type
        )
        return f"{settings.MINIO_BUCKET_NAME}/{object_name}"
    
    def get_presigned_put_url(self, object_name: str, content_type: str) -> str:
        """Generate a pre-signed URL for uploading a file."""
        return self.client.presigned_put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            expires=3600  # URL valido per 1 ora
        )
    
    def get_presigned_get_url(self, object_name: str) -> str:
        """Generate a pre-signed URL for downloading a file."""
        return self.client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            expires=3600  # URL valido per 1 ora
        )
    
    def get_file_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of file data."""
        import hashlib
        return hashlib.sha256(data).hexdigest()

def get_minio_service() -> MinioService:
    """Dependency for getting a MinIO service instance."""
    return MinioService()

# Crea un'istanza singleton del servizio
# minio_service = MinioService() 