import redis
from typing import Optional
import json
from pydantic import BaseModel
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis client instance
redis_client: Optional[redis.Redis] = None

def get_redis_client():
    """Crea e restituisce un client Redis."""
    global redis_client
    
    # Se il client è già inizializzato, restituiscilo
    if redis_client is not None:
        return redis_client
    
    try:
        # Se REDIS_URL non è configurato, restituisci None
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL non configurato - Redis disabilitato")
            return None
            
        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        # Test della connessione
        client.ping()
        logger.debug("Connessione Redis stabilita con successo")
        redis_client = client
        return client
    except Exception as e:
        logger.error(f"Errore nella connessione a Redis: {str(e)}")
        # Non sollevare l'eccezione, restituisci None
        return None

def cache_user(user: BaseModel, email: str, expire_seconds: int = 300) -> None:
    """Cache user data in Redis."""
    redis = get_redis_client()
    if redis is None:
        logger.warning("Redis non disponibile - cache disabilitata")
        return
    key = f"user:{email}"
    redis.setex(key, expire_seconds, user.model_dump_json())

def get_cached_user(email: str) -> Optional[BaseModel]:
    """Get cached user data from Redis."""
    redis = get_redis_client()
    if redis is None:
        return None
    key = f"user:{email}"
    data = redis.get(key)
    return json.loads(data) if data else None 