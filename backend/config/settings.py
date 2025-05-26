from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() == "true"
    MINIO_BUCKET_MANUALS: str = os.getenv("MINIO_BUCKET_MANUALS", "eterna-manuals")
    MINIO_BUCKET_AUDIO: str = os.getenv("MINIO_BUCKET_AUDIO", "eterna-audio")
    MINIO_BUCKET_LEGACY: str = os.getenv("MINIO_BUCKET_LEGACY", "eterna-legacy")
    MINIO_POOL_SIZE: int = int(os.getenv("MINIO_POOL_SIZE", "10"))
    MINIO_TIMEOUT: int = int(os.getenv("MINIO_TIMEOUT", "30"))
    MINIO_BACKUP_ENABLED: bool = os.getenv("MINIO_BACKUP_ENABLED", "True").lower() == "true"
    MINIO_BACKUP_FREQUENCY: str = os.getenv("MINIO_BACKUP_FREQUENCY", "daily")
    MINIO_BACKUP_RETENTION: int = int(os.getenv("MINIO_BACKUP_RETENTION", "30"))
    MINIO_ENCRYPTION_ENABLED: bool = os.getenv("MINIO_ENCRYPTION_ENABLED", "True").lower() == "true"
    MINIO_ENCRYPTION_KEY: str = os.getenv("MINIO_ENCRYPTION_KEY", "your-encryption-key-here")
    MINIO_CACHE_ENABLED: bool = os.getenv("MINIO_CACHE_ENABLED", "True").lower() == "true"
    MINIO_CACHE_TTL: int = int(os.getenv("MINIO_CACHE_TTL", "3600"))

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 