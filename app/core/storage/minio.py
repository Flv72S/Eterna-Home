import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from app.core.config import settings
import logging
import hashlib
from typing import Optional, Tuple

# Configurazione logger
logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        """Inizializza il client MinIO con le configurazioni specificate."""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.MINIO_REGION,
                use_ssl=settings.MINIO_USE_SSL,
                verify=True  # Verifica certificati SSL
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            self._ensure_bucket_exists()
            self._setup_lifecycle_policy()
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

    def _ensure_bucket_exists(self) -> None:
        """Verifica l'esistenza del bucket e lo crea se necessario."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': settings.MINIO_REGION}
                    )
                    logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {str(create_error)}")
                    raise
            else:
                logger.error(f"Error checking bucket: {str(e)}")
                raise

    def _setup_lifecycle_policy(self) -> None:
        """Configura le policy di lifecycle per la gestione automatica dei file."""
        try:
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'DeleteOldVersions',
                        'Status': 'Enabled',
                        'Filter': {
                            'Prefix': ''
                        },
                        'Expiration': {
                            'Days': settings.MINIO_LIFECYCLE_DAYS
                        }
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            logger.info(f"Lifecycle policy configured for {settings.MINIO_LIFECYCLE_DAYS} days")
        except ClientError as e:
            logger.error(f"Failed to set lifecycle policy: {str(e)}")
            raise

    async def upload_file(self, file: UploadFile, object_name: Optional[str] = None) -> Tuple[str, str]:
        """Carica un file su MinIO e restituisce l'URL e il checksum."""
        if object_name is None:
            object_name = file.filename

        try:
            content = await file.read()
            checksum = hashlib.md5(content).hexdigest()
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=content,
                ContentType=file.content_type,
                Metadata={'checksum': checksum}
            )
            
            url = f"{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"
            logger.info(f"File {object_name} uploaded successfully")
            return url, checksum
        except Exception as e:
            logger.error(f"Failed to upload file {object_name}: {str(e)}")
            raise

    async def download_file(self, object_name: str) -> Tuple[bytes, str]:
        """Scarica un file da MinIO e verifica il checksum."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            content = response['Body'].read()
            stored_checksum = response.get('Metadata', {}).get('checksum', '')
            calculated_checksum = hashlib.md5(content).hexdigest()
            
            if stored_checksum and stored_checksum != calculated_checksum:
                logger.error(f"Checksum mismatch for {object_name}")
                raise ValueError("File integrity check failed")
            
            logger.info(f"File {object_name} downloaded successfully")
            return content, calculated_checksum
        except ClientError as e:
            logger.error(f"Failed to download file {object_name}: {str(e)}")
            raise

    def object_exists(self, object_name: str) -> bool:
        """Verifica se un oggetto esiste nel bucket."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"Object {object_name} exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"Object {object_name} does not exist")
                return False
            logger.error(f"Error checking object {object_name}: {str(e)}")
            raise

    def delete_file(self, object_name: str) -> None:
        """Elimina un file da MinIO."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File {object_name} deleted successfully")
        except ClientError as e:
            logger.error(f"Failed to delete file {object_name}: {str(e)}")
            raise

# Lazy loading: provide a function to get the MinioClient instance only when needed
def get_minio_client():
    return MinioClient() 