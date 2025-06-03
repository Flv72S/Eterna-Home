import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile
import hashlib
from typing import Optional, Tuple
import os

from app.core.config import settings

class MinioClient:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=settings.MINIO_REGION
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Verifica che il bucket esista, altrimenti lo crea."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self.client.create_bucket(Bucket=self.bucket_name)
            else:
                raise

    def object_exists(self, minio_path: str) -> bool:
        """
        Verifica se un oggetto esiste nel bucket.
        
        Args:
            minio_path: Path dell'oggetto su MinIO
            
        Returns:
            bool: True se l'oggetto esiste, False altrimenti
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=minio_path
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    async def upload_file(
        self,
        file: UploadFile,
        house_id: int,
        document_id: int
    ) -> Tuple[str, str]:
        """
        Carica un file su MinIO.
        
        Args:
            file: Il file da caricare
            house_id: ID della casa
            document_id: ID del documento
            
        Returns:
            Tuple[str, str]: (path del file su MinIO, checksum SHA256)
        """
        # Calcola il checksum SHA256
        file_content = await file.read()
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Costruisci il path del file
        file_extension = os.path.splitext(file.filename)[1]
        minio_path = f"{house_id}/{document_id}{file_extension}"
        
        # Carica il file su MinIO
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=minio_path,
            Body=file_content,
            ContentType=file.content_type
        )
        
        return minio_path, checksum

    def get_file_url(self, minio_path: str) -> str:
        """Genera l'URL per il download del file."""
        return f"{settings.MINIO_ENDPOINT}/{self.bucket_name}/{minio_path}"

    def download_file(self, minio_path: str) -> Optional[bytes]:
        """
        Scarica un file da MinIO.
        
        Args:
            minio_path: Path del file su MinIO
            
        Returns:
            bytes: Contenuto del file, None se non trovato
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=minio_path
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def delete_file(self, minio_path: str) -> bool:
        """
        Elimina un file da MinIO.
        
        Args:
            minio_path: Path del file su MinIO
            
        Returns:
            bool: True se il file è stato eliminato, False se non esisteva
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=minio_path
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False
            raise

# Istanza singleton del client MinIO
# minio_client = MinioClient() 