import fakeredis
import pytest
from app.core.config import settings

@pytest.fixture(scope="session")
def redis_client():
    """Crea un client Redis fittizio per i test."""
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server)
    return client

@pytest.fixture(autouse=True)
def override_redis_settings():
    """Override delle impostazioni Redis per i test."""
    original_host = settings.REDIS_HOST
    original_port = settings.REDIS_PORT
    settings.REDIS_HOST = "localhost"
    settings.REDIS_PORT = 6379
    yield
    settings.REDIS_HOST = original_host
    settings.REDIS_PORT = original_port 