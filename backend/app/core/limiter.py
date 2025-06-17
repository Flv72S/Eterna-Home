from slowapi import Limiter
from slowapi.util import get_remote_address

# Inizializza il limiter con il limite di 5 richieste al minuto per IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/minute"],
    application_limits=["100/minute"],
    headers_enabled=True,
    storage_uri="memory://",
    strategy="fixed-window",
    auto_check=True,
    swallow_errors=False,
    in_memory_fallback=["3/minute"],
    in_memory_fallback_enabled=True,
    retry_after="http-date",
    key_prefix="rate_limit",
    enabled=True
) 