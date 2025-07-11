"""
Configurazione locale per test avanzati - sovrascrive conftest.py globale.
"""
import pytest
import sys
from unittest.mock import Mock

# Mock delle dipendenze globali che potrebbero non essere disponibili
@pytest.fixture(autouse=True)
def mock_global_dependencies():
    """Mock automatico delle dipendenze globali."""
    # Mock per app.core.redis se non disponibile
    if 'app.core.redis' not in sys.modules:
        mock_redis = Mock()
        mock_redis.get_redis_client = Mock(return_value=Mock())
        sys.modules['app.core.redis'] = mock_redis
    
    # Mock per altre dipendenze se necessario
    if 'app.core.database' not in sys.modules:
        mock_db = Mock()
        sys.modules['app.core.database'] = mock_db
    
    yield

# Configurazione pytest per i test avanzati
def pytest_configure(config):
    """Configurazione pytest per test avanzati."""
    config.addinivalue_line(
        "markers", "advanced: mark test as advanced implementation test"
    )

def pytest_collection_modifyitems(config, items):
    """Aggiunge marker 'advanced' a tutti i test in questa directory."""
    for item in items:
        item.add_marker(pytest.mark.advanced) 