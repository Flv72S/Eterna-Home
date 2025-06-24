"""
Middleware per il logging delle richieste API con Trace ID e supporto multi-tenant.
"""
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger, set_trace_id, clear_trace_id
from app.core.logging_multi_tenant import (
    multi_tenant_logger,
    set_tenant_context,
    clear_tenant_context
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware per il logging delle richieste API con supporto multi-tenant."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Genera Trace ID per la richiesta
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)
        
        # Estrai tenant_id e user_id dagli headers (se disponibili)
        tenant_id = request.headers.get("X-Tenant-ID")
        user_id = request.headers.get("X-User-ID")
        
        # Imposta il contesto del tenant per il logging
        if tenant_id:
            try:
                tenant_uuid = uuid.UUID(tenant_id)
                set_tenant_context(tenant_uuid, int(user_id) if user_id else None)
            except (ValueError, TypeError):
                # Se i valori non sono validi, non impostare il contesto
                pass
        
        # Log della richiesta in arrivo
        start_time = time.time()
        
        # Log con sistema multi-tenant
        extra_fields = {
            "event": "api_request_started",
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "trace_id": trace_id
        }
        
        multi_tenant_logger.info("API request started", extra_fields)
        
        # Log anche con il sistema legacy per compatibilità
        logger.info("API request started",
                    method=request.method,
                    url=str(request.url),
                    path=request.url.path,
                    query_params=dict(request.query_params),
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    trace_id=trace_id)
        
        try:
            # Processa la richiesta
            response = await call_next(request)
            
            # Calcola il tempo di risposta
            process_time = time.time() - start_time
            
            # Log della risposta con sistema multi-tenant
            response_extra_fields = {
                "event": "api_request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "trace_id": trace_id
            }
            
            multi_tenant_logger.info("API request completed", response_extra_fields)
            
            # Log anche con il sistema legacy
            logger.info("API request completed",
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        process_time=round(process_time, 4),
                        trace_id=trace_id)
            
            # Aggiungi Trace ID all'header della risposta
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # Calcola il tempo di risposta
            process_time = time.time() - start_time
            
            # Log dell'errore con sistema multi-tenant
            error_extra_fields = {
                "event": "api_request_failed",
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time": round(process_time, 4),
                "trace_id": trace_id
            }
            
            multi_tenant_logger.error("API request failed", error_extra_fields)
            
            # Log anche con il sistema legacy
            logger.error("API request failed",
                         method=request.method,
                         path=request.url.path,
                         error=str(e),
                         process_time=round(process_time, 4),
                         trace_id=trace_id,
                         exc_info=True)
            
            # Rilancia l'eccezione
            raise
        finally:
            # Pulisci il Trace ID e il contesto del tenant
            clear_trace_id()
            clear_tenant_context()


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware per il logging degli errori non gestiti con supporto multi-tenant."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log dell'errore con sistema multi-tenant
            error_extra_fields = {
                "event": "unhandled_exception",
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "error_type": type(e).__name__,
                "trace_id": getattr(request.state, 'trace_id', None)
            }
            
            multi_tenant_logger.error("Unhandled exception in request", error_extra_fields)
            
            # Log anche con il sistema legacy
            logger.error("Unhandled exception in request",
                         method=request.method,
                         path=request.url.path,
                         error=str(e),
                         error_type=type(e).__name__,
                         trace_id=getattr(request.state, 'trace_id', None),
                         exc_info=True)
            raise


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware per il logging degli eventi di sicurezza."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log tentativi di accesso a endpoint sensibili
        sensitive_paths = ["/api/v1/admin", "/api/v1/users", "/api/v1/ai"]
        
        if any(path in request.url.path for path in sensitive_paths):
            extra_fields = {
                "event": "sensitive_endpoint_access",
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
            
            multi_tenant_logger.log_security_event("Sensitive endpoint access", extra_fields)
        
        return await call_next(request) 