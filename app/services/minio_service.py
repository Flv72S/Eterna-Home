import os
import uuid
import logging
from datetime import datetime
from typing import Optional, Tuple
from minio import Minio
from minio.error import S3Error
import mimetypes

# Configurazione logger
logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        self.client = self._get_client()
        self.default_bucket = os.getenv('MINIO_DEFAULT_BUCKET', 'default-bucket')
        self._ensure_bucket_exists(self.default_bucket)

    def _get_client(self):
        """Create and return a Minio client instance."""
        try:
            client = Minio(
                os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            return client
        except Exception as e:
            logger.error(f"Error creating Minio client: {str(e)}")
            raise

    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure that the specified bucket exists."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}")
            raise

    def _get_content_type(self, filename: str) -> str:
        """Get the content type for a file based on its extension."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'

    def _generate_object_name(self, filename: str, folder: str = None) -> str:
        """Generate a unique object name for the file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        base_name = os.path.basename(filename)
        name, ext = os.path.splitext(base_name)
        
        if folder:
            return f"{folder}/{timestamp}_{unique_id}_{name}{ext}"
        return f"{timestamp}_{unique_id}_{name}{ext}"

    def upload_file(self, data: bytes, filename: str, bucket_name: str = None, folder: str = None) -> str:
        """
        Upload a file to Minio.
        
        Args:
            data (bytes): File content as bytes
            filename (str): Original filename
            bucket_name (str, optional): Name of the bucket. Defaults to None.
            folder (str, optional): Folder path within the bucket. Defaults to None.
            
        Returns:
            str: The object name of the uploaded file
            
        Raises:
            S3Error: If there's an error during upload
        """
        try:
            bucket = bucket_name or self.default_bucket
            self._ensure_bucket_exists(bucket)
            
            object_name = self._generate_object_name(filename, folder)
            content_type = self._get_content_type(filename)
            
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data,
                length=len(data),
                content_type=content_type
            )
            
            logger.info(f"Successfully uploaded {filename} to {bucket}/{object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file to Minio: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {str(e)}")
            raise
    
    def get_presigned_put_url(self, object_name: str, content_type: str) -> str:
        """Generate a pre-signed URL for uploading a file."""
        return self.client.presigned_put_object(
            bucket_name=self.default_bucket,
            object_name=object_name,
            expires=3600  # URL valido per 1 ora
        )
    
    def get_presigned_get_url(self, object_name: str) -> str:
        """Generate a pre-signed URL for downloading a file."""
        return self.client.presigned_get_object(
            bucket_name=self.default_bucket,
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