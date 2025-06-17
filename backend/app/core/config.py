from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Eterna Home"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test"
    
    # Superuser settings
    FIRST_SUPERUSER: str = "admin@eternahome.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"

    # CORS origins
    CORS_ORIGINS: list[str] = ["*"]
    
    # Configurazione Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

settings = Settings()