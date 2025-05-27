import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class CloudSettings(BaseSettings):
    # Configurazioni Database
    database_url: str
    
    # Configurazioni JWT
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    # Configurazioni Connessione MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False  # True per connessioni HTTPS
    
    # Nomi dei Bucket
    MINIO_BUCKET_MANUALS: str = "eterna-manuals"
    MINIO_BUCKET_AUDIO: str = "eterna-audio"
    MINIO_BUCKET_LEGACY: str = "eterna-legacy"
    MINIO_BUCKET_BIM: str = "eterna-bim"
    
    # Configurazioni Scalabilità
    MINIO_POOL_SIZE: int = 10  # Dimensione del pool di connessioni
    MINIO_TIMEOUT: int = 30    # Timeout in secondi
    
    # Configurazioni Backup
    MINIO_BACKUP_ENABLED: bool = True
    MINIO_BACKUP_FREQUENCY: str = "daily"  # frequenza: daily (giornaliero), weekly (settimanale), monthly (mensile)
    MINIO_BACKUP_RETENTION: int = 30  # giorni di conservazione dei backup
    
    # Configurazioni Crittografia
    MINIO_ENCRYPTION_ENABLED: bool = True
    MINIO_ENCRYPTION_KEY: str  # Chiave di crittografia AES
    
    # Configurazioni Cache
    MINIO_CACHE_ENABLED: bool = True
    MINIO_CACHE_TTL: int = 3600  # Durata della cache in secondi
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings():
    return CloudSettings()

# Crea un'istanza singleton
settings = get_settings() 