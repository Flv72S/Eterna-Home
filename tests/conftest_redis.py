import pytest
from fakeredis import FakeRedis
from app.core.redis import get_redis_client
import logging

logger = logging.getLogger(__name__)

# Crea un'istanza di FakeRedis per i test
redis_client = FakeRedis(
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5
)

@pytest.fixture(autouse=True)
def override_redis_client():
    """Override Redis client with FakeRedis for testing."""
    logger.debug("Setting up FakeRedis for tests...")
    original_client = get_redis_client()
    
    # Sostituisci il client Redis con FakeRedis
    import app.core.redis
    app.core.redis.redis_client = redis_client
    
    yield redis_client
    
    # Ripristina il client Redis originale
    app.core.redis.redis_client = original_client
    logger.debug("Restored original Redis client")