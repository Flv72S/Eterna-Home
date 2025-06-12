from typing import Optional, List
from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./eterna_home.db"
    SQL_ECHO: bool = False
    
    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TEST_TOKEN: str = "test-token"  # Token di test per i test automatizzati
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Eterna Home"
    VERSION: str = "1.0.0"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # MinIO
    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_REGION: str = "us-east-1"
    MINIO_BUCKET_NAME: str = "eterna-home"
    MINIO_USE_SSL: bool = False  # Abilita HTTPS
    MINIO_SECURE: bool = False  # <--- AGGIUNTO QUI
    MINIO_LIFECYCLE_DAYS: int = 180  # Giorni prima dell'eliminazione automatica
    
    # Upload settings
    MAX_DIRECT_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }

settings = Settings()

def get_settings() -> Settings:
    """
    Dependency per ottenere le impostazioni dell'applicazione.
    
    Returns:
        Settings: Istanza delle impostazioni
    """
    return settings 