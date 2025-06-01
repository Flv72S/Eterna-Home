from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator, ConfigDict
import secrets
from functools import lru_cache

class Settings(BaseSettings):
    # Configurazione del modello
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        json_schema_extra={
            "example": {
                "PROJECT_NAME": "Eterna Home",
                "VERSION": "0.1.0",
                "API_V1_STR": "/api/v1",
                "ENVIRONMENT": "development",
                "DEBUG": True,
                "SECRET_KEY": "your-secret-key",
                "ACCESS_TOKEN_EXPIRE_MINUTES": 11520,
                "ALGORITHM": "HS256",
                "POSTGRES_SERVER": "localhost",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "your-password",
                "POSTGRES_DB": "eterna_home",
                "POSTGRES_PORT": "5432",
                "DB_POOL_SIZE": 20,
                "DB_MAX_OVERFLOW": 10,
                "DB_POOL_TIMEOUT": 30,
                "DB_POOL_RECYCLE": 1800,
                "DB_ECHO": False,
                "DB_USE_ASYNC": False,
                "BACKEND_CORS_ORIGINS": ["http://localhost:3000", "http://localhost:8000"],
                "LOG_LEVEL": "INFO",
                "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    )

    # Configurazione base
    PROJECT_NAME: str = "Eterna Home"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Ambiente
    ENVIRONMENT: str = "development"  # development, testing, production
    DEBUG: bool = True
    
    # Sicurezza
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "N0nn0c4rl0!!"
    POSTGRES_DB: str = "eterna_home"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Database Pool Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False
    
    # Async Database Settings
    DB_USE_ASYNC: bool = False
    ASYNC_DATABASE_URI: Optional[str] = None

    @field_validator("DEBUG", mode="after")
    @classmethod
    def set_debug_for_production(cls, v, info):
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            return False
        return v

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return str(PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT")),
            path=values.get('POSTGRES_DB') or '',
        ))

    @field_validator("ASYNC_DATABASE_URI", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT")),
            path=values.get('POSTGRES_DB') or '',
        ))

    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @property
    def get_async_database_url(self) -> str:
        if self.ASYNC_DATABASE_URI:
            return self.ASYNC_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@lru_cache()
def get_settings() -> Settings:
    """
    Restituisce un'istanza cached delle impostazioni.
    Questo evita di ricaricare il file .env ad ogni accesso.
    """
    return Settings()

# Istanza globale delle impostazioni
settings = get_settings()
