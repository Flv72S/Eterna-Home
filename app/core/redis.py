from redis import Redis
from typing import Optional
import json
from pydantic import BaseModel

# Redis client instance
redis_client: Optional[Redis] = None

def get_redis_client() -> Redis:
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
    return redis_client

def cache_user(user: BaseModel, email: str, expire_seconds: int = 300) -> None:
    """Cache user data in Redis."""
    redis = get_redis_client()
    key = f"user:{email}"
    redis.setex(key, expire_seconds, user.model_dump_json())

def get_cached_user(email: str) -> Optional[BaseModel]:
    """Get cached user data from Redis."""
    redis = get_redis_client()
    key = f"user:{email}"
    data = redis.get(key)
    return json.loads(data) if data else None 