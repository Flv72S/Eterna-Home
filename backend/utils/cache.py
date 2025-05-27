"""
Cache utility module for Eterna Home backend.
Provides simple in-memory caching functionality.
"""

from typing import Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache = {}

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve a value from the cache.
    
    Args:
        key (str): The cache key
        
    Returns:
        Optional[Any]: The cached value if found and not expired, None otherwise
    """
    if key not in _cache:
        return None
        
    value, expiry = _cache[key]
    if expiry and datetime.now() > expiry:
        del _cache[key]
        return None
        
    return value

def set_cache(key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
    """
    Store a value in the cache.
    
    Args:
        key (str): The cache key
        value (Any): The value to cache
        ttl_seconds (Optional[int]): Time to live in seconds, None for no expiration
    """
    expiry = None
    if ttl_seconds is not None:
        expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    
    _cache[key] = (value, expiry)
    logger.debug(f"Cached value for key: {key}") 