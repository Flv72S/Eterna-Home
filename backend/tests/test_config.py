import pytest
from app.core.config import Settings, get_settings

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
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="test_db",
        POSTGRES_PORT="5432"
    )
    assert str(settings.get_database_url).startswith("postgresql://")
    assert "test_user" in str(settings.get_database_url)
    assert "test_db" in str(settings.get_database_url)

def test_settings_caching():
    """Test che verifica il caching delle impostazioni"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2  # Verifica che sia la stessa istanza

def test_environment_specific_settings():
    """Test che verifica le impostazioni specifiche per ambiente"""
    settings = Settings(ENVIRONMENT="production")
    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False  # In produzione DEBUG dovrebbe essere False 