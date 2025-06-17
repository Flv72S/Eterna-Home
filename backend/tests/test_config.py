import pytest
from app.core.config import Settings, settings

def test_settings():
    assert settings.PROJECT_NAME == "Eterna Home"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.SECRET_KEY == "your-secret-key-here"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.DATABASE_URL == "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable"
    assert settings.FIRST_SUPERUSER == "admin@eternahome.com"
    assert settings.FIRST_SUPERUSER_PASSWORD == "admin123"

def test_settings_creation():
    """Test che verifica la creazione corretta delle impostazioni"""
    settings = Settings()
    assert settings.PROJECT_NAME == "Eterna Home"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True

def test_database_url_assembly():
    """Test che verifica l'assemblaggio corretto dell'URL del database"""
    settings = Settings(
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="eterna_home_test",
        POSTGRES_PORT="5432"
    )
    assert str(settings.database_url).startswith("postgresql://")
    assert "postgres" in str(settings.database_url)
    assert "eterna_home_test" in str(settings.database_url)

def test_settings_caching():
    """Test che verifica il caching delle impostazioni"""
    settings1 = settings
    settings2 = settings
    assert settings1 is settings2  # Verifica che sia la stessa istanza

def test_environment_specific_settings():
    """Test che verifica le impostazioni specifiche per ambiente"""
    settings = Settings(ENVIRONMENT="production")
    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False  # In produzione DEBUG dovrebbe essere False 