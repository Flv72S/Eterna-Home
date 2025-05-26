import os
from pydantic_settings import BaseSettings

class CloudSettings(BaseSettings):
    # MinIO Connection Settings
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False  # True per HTTPS
    
    # Bucket Names
    MINIO_BUCKET_MANUALS: str = "eterna-manuals"
    MINIO_BUCKET_AUDIO: str = "eterna-audio"
    MINIO_BUCKET_LEGACY: str = "eterna-legacy"
    
    # Scalability Settings
    MINIO_POOL_SIZE: int = 10  # Connection pool size
    MINIO_TIMEOUT: int = 30    # Timeout in seconds
    
    # Backup Settings
    MINIO_BACKUP_ENABLED: bool = True
    MINIO_BACKUP_FREQUENCY: str = "daily"  # daily, weekly, monthly
    MINIO_BACKUP_RETENTION: int = 30  # days to keep backups
    
    # Encryption Settings
    MINIO_ENCRYPTION_ENABLED: bool = True
    MINIO_ENCRYPTION_KEY: str  # AES encryption key
    
    # Cache Settings
    MINIO_CACHE_ENABLED: bool = True
    MINIO_CACHE_TTL: int = 3600  # Cache time-to-live in seconds
    
    class Config:
        env_file = ".env"  # Per caricare variabili da un file .env
        env_file_encoding = "utf-8"

# Create a singleton instance
settings = CloudSettings() 