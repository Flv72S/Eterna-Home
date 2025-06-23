import os
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
import logging

# Configurazione logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    PROJECT_NAME: str = "Eterna Home"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"  # Cambiare in produzione
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 100
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "default-bucket"
    MINIO_REGION: str = "us-east-1"
    MINIO_USE_SSL: bool = False
    MINIO_LIFECYCLE_DAYS: int = 30
    
    # Token di test fisso per evitare problemi di timing nei test
    TEST_TOKEN: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzM1NjgwMDAwfQ.test_signature"
    
    # BIM Conversion Settings
    USE_REAL_BIM_CONVERSION: bool = Field(default=False, description="Usa conversioni BIM reali invece di simulazioni")
    USE_IFCOPENSHELL: bool = Field(default=False, description="Usa IfcOpenShell per conversione IFC")
    USE_FORGE_SDK: bool = Field(default=False, description="Usa Forge SDK per conversione RVT")
    
    # IfcOpenShell Settings
    IFC_CONVERSION_TIMEOUT: int = Field(default=1800, description="Timeout conversione IFC in secondi")
    IFC_MAX_FILE_SIZE: int = Field(default=500 * 1024 * 1024, description="Dimensione massima file IFC (500MB)")
    
    # Forge SDK Settings
    FORGE_CLIENT_ID: str = Field(default="", description="Autodesk Forge Client ID")
    FORGE_CLIENT_SECRET: str = Field(default="", description="Autodesk Forge Client Secret")
    FORGE_BUCKET_NAME: str = Field(default="eterna-home-bim", description="Bucket Forge per file BIM")
    FORGE_REGION: str = Field(default="us", description="Regione Forge (us, eu, emea)")
    
    # Conversion Quality Settings
    BIM_CONVERSION_QUALITY: str = Field(default="medium", description="Qualità conversione (low, medium, high)")
    GLTF_OPTIMIZATION: bool = Field(default=True, description="Ottimizza file GLTF per web")
    
    # Notification Settings
    ENABLE_CONVERSION_NOTIFICATIONS: bool = Field(default=False, description="Abilita notifiche conversione")
    NOTIFICATION_EMAIL: bool = Field(default=False, description="Notifiche via email")
    NOTIFICATION_WEBSOCKET: bool = Field(default=False, description="Notifiche real-time WebSocket")
    
    # Speech-to-Text Settings
    USE_REAL_SPEECH_TO_TEXT: bool = Field(default=False, description="Usa servizi di trascrizione audio reali")
    GOOGLE_SPEECH_ENABLED: bool = Field(default=False, description="Abilita Google Speech-to-Text")
    AZURE_SPEECH_ENABLED: bool = Field(default=False, description="Abilita Azure Speech Services")
    
    # Google Speech-to-Text Settings
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="", description="Path al file credentials Google")
    GOOGLE_SPEECH_LANGUAGE: str = Field(default="it-IT", description="Lingua default per trascrizione")
    GOOGLE_SPEECH_MODEL: str = Field(default="latest_long", description="Modello Google Speech (latest_long, latest_short)")
    
    # Azure Speech Services Settings
    AZURE_SPEECH_KEY: str = Field(default="", description="Azure Speech Services API Key")
    AZURE_SPEECH_REGION: str = Field(default="westeurope", description="Azure Speech Services Region")
    AZURE_SPEECH_LANGUAGE: str = Field(default="it-IT", description="Lingua default per Azure Speech")
    
    # Voice Processing Settings
    VOICE_PROCESSING_TIMEOUT: int = Field(default=300, description="Timeout elaborazione vocale in secondi")
    VOICE_MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="Dimensione massima file audio (50MB)")
    VOICE_SUPPORTED_FORMATS: list[str] = Field(default=["wav", "mp3", "m4a", "flac"], description="Formati audio supportati")
    
    # Local Interface Settings
    ENABLE_LOCAL_INTERFACES: bool = Field(default=True, description="Abilita interfacce locali")
    LOCAL_INTERFACE_PORT: int = Field(default=8080, description="Porta interfacce locali")
    LOCAL_INTERFACE_HOST: str = Field(default="0.0.0.0", description="Host interfacce locali")
    
    # Voice Command Integration Settings
    ENABLE_VOICE_COMMANDS: bool = Field(default=True, description="Abilita comandi vocali")
    VOICE_COMMAND_TIMEOUT: int = Field(default=30, description="Timeout comando vocale in secondi")
    VOICE_COMMAND_LANGUAGE: str = Field(default="it-IT", description="Lingua comandi vocali")
    
    # Integration Settings
    ENABLE_IOT_INTEGRATION: bool = Field(default=True, description="Abilita integrazione IoT")
    ENABLE_BIM_INTEGRATION: bool = Field(default=True, description="Abilita integrazione BIM")
    ENABLE_DOCUMENT_INTEGRATION: bool = Field(default=True, description="Abilita integrazione documenti")
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()