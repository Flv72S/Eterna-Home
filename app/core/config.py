from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./eterna_home.db"
    SQL_ECHO: bool = False
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"  # In produzione, usare una chiave sicura
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Eterna Home"
    
    class Config:
        case_sensitive = True

settings = Settings() 