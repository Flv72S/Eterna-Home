"""
Sistema di Rate Limiting avanzato per Eterna Home.
Gestisce limitazioni per IP con configurazioni specifiche per endpoint critici.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging_multi_tenant import multi_tenant_logger

# Configurazione logger
logger = logging.getLogger(__name__)

class SecurityLimiter:
    """
    Limiter avanzato con configurazioni specifiche per endpoint critici
    e logging degli eventi di sicurezza.
    """
    
    def __init__(self):
        """Inizializza il limiter con configurazioni di sicurezza."""
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200/minute", "1000/hour"] if settings.ENABLE_RATE_LIMITING else []
        )
        
        # Configurazioni specifiche per endpoint critici
        self.critical_endpoints = {
            "/api/v1/auth/token": {
                "limit": "5/minute",
                "description": "Login endpoint - protezione brute force"
            },
            "/api/v1/voice/commands": {
                "limit": "10/minute", 
                "description": "Voice commands - protezione spam"
            },
            "/api/v1/documents/upload": {
                "limit": "3/minute",
                "description": "Document upload - protezione storage abuse"
            },
            "/api/v1/ai-assistant/chat": {
                "limit": "20/minute",
                "description": "AI chat - protezione costi API"
            },
            "/api/v1/bim/upload": {
                "limit": "2/minute",
                "description": "BIM upload - protezione conversione costosa"
            }
        }
        
        # Statistiche per monitoring
        self.blocked_ips: Dict[str, Dict[str, Any]] = {}
    
    def get_limit_for_endpoint(self, endpoint: str) -> Optional[str]:
        """Restituisce il limite specifico per un endpoint."""
        return self.critical_endpoints.get(endpoint, {}).get("limit")
    
    def log_rate_limit_exceeded(self, request: Request, endpoint: str, ip: str):
        """Logga un evento di rate limit exceeded."""
        endpoint_config = self.critical_endpoints.get(endpoint, {})
        
        # Aggiorna statistiche
        if ip not in self.blocked_ips:
            self.blocked_ips[ip] = {
                "first_blocked": None,
                "last_blocked": None,
                "total_blocks": 0,
                "endpoints": {}
            }
        
        self.blocked_ips[ip]["total_blocks"] += 1
        self.blocked_ips[ip]["last_blocked"] = "now"  # Sarebbe meglio un timestamp
        
        if endpoint not in self.blocked_ips[ip]["endpoints"]:
            self.blocked_ips[ip]["endpoints"][endpoint] = 0
        self.blocked_ips[ip]["endpoints"][endpoint] += 1
        
        # Log dell'evento
        multi_tenant_logger.log_security_event(
            "rate_limit_exceeded",
            {
                "ip_address": ip,
                "endpoint": endpoint,
                "user_agent": request.headers.get("user-agent", ""),
                "description": endpoint_config.get("description", "Unknown endpoint"),
                "total_blocks_for_ip": self.blocked_ips[ip]["total_blocks"]
            }
        )
        
        logger.warning(
            f"Rate limit exceeded for IP {ip} on endpoint {endpoint}",
            extra={
                "ip_address": ip,
                "endpoint": endpoint,
                "user_agent": request.headers.get("user-agent", ""),
                "event_type": "rate_limit_exceeded"
            }
        )
    
    def create_rate_limit_response(self, request: Request) -> JSONResponse:
        """Crea una risposta personalizzata per rate limit exceeded."""
        ip = get_remote_address(request)
        endpoint = request.url.path
        
        # Log dell'evento
        self.log_rate_limit_exceeded(request, endpoint, ip)
        
        # Risposta personalizzata
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60,  # secondi
                "endpoint": endpoint
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Reset": "60"
            }
        )
    
    def get_blocked_ips_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche sugli IP bloccati."""
        return {
            "total_blocked_ips": len(self.blocked_ips),
            "total_blocks": sum(ip_data["total_blocks"] for ip_data in self.blocked_ips.values()),
            "most_blocked_endpoints": self._get_most_blocked_endpoints(),
            "recent_blocks": self._get_recent_blocks()
        }
    
    def _get_most_blocked_endpoints(self) -> Dict[str, int]:
        """Calcola gli endpoint più bloccati."""
        endpoint_counts = {}
        for ip_data in self.blocked_ips.values():
            for endpoint, count in ip_data["endpoints"].items():
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + count
        return dict(sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _get_recent_blocks(self) -> list:
        """Restituisce i blocchi recenti (ultimi 10)."""
        # Semplificato - in produzione userebbe timestamp reali
        recent = []
        for ip, data in list(self.blocked_ips.items())[-10:]:
            recent.append({
                "ip": ip,
                "total_blocks": data["total_blocks"],
                "endpoints": data["endpoints"]
            })
        return recent

# Istanza globale del limiter
security_limiter = SecurityLimiter()

# Decoratori per rate limiting specifico
def rate_limit_auth():
    """Rate limit per endpoint di autenticazione."""
    if not settings.ENABLE_RATE_LIMITING:
        return lambda func: func
    
    return security_limiter.limiter.limit("5/minute")

def rate_limit_voice():
    """Rate limit per comandi vocali."""
    if not settings.ENABLE_RATE_LIMITING:
        return lambda func: func
    
    return security_limiter.limiter.limit("10/minute")

def rate_limit_upload():
    """Rate limit per upload di file."""
    if not settings.ENABLE_RATE_LIMITING:
        return lambda func: func
    
    return security_limiter.limiter.limit("3/minute")

def rate_limit_ai():
    """Rate limit per endpoint AI."""
    if not settings.ENABLE_RATE_LIMITING:
        return lambda func: func
    
    return security_limiter.limiter.limit("20/minute")

def rate_limit_bim():
    """Rate limit per upload BIM."""
    if not settings.ENABLE_RATE_LIMITING:
        return lambda func: func
    
    return security_limiter.limiter.limit("2/minute")

# Middleware per gestione rate limit
async def rate_limit_middleware(request: Request, call_next):
    """Middleware per gestione rate limit con logging."""
    try:
        response = await call_next(request)
        return response
    except RateLimitExceeded:
        return security_limiter.create_rate_limit_response(request)

# Funzione per ottenere statistiche (per endpoint admin)
def get_rate_limit_stats():
    """Restituisce statistiche del rate limiting."""
    return security_limiter.get_blocked_ips_stats() 