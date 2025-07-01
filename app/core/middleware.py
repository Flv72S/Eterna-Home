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
from app.core.logging_config import (
    get_logger,
    set_context,
    clear_context,
    log_security_event,
    log_operation
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware per logging automatico delle richieste HTTP.
    Include contesto multi-tenant e tracciamento delle operazioni.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Genera ID univoci per la request
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        
        # Inizializza il contesto
        set_context(trace_id=trace_id, request_id=request_id)
        
        # Log dell'inizio della request
        start_time = time.time()
        
        # Estrai informazioni dalla request
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log della request in arrivo
        logger.info(
            "Request started",
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
            event_name="request_started",
            status="started"
        )
        
        try:
            # Processa la request
            response = await call_next(request)
            
            # Calcola durata
            duration = time.time() - start_time
            
            # Log del completamento
            logger.info(
                "Request completed",
                method=method,
                url=url,
                status_code=response.status_code,
                duration=duration,
                event_name="request_completed",
                status="success" if response.status_code < 400 else "failed"
            )
            
            # Log operazioni specifiche
            await self._log_specific_operations(request, response, duration)
            
            return response
            
        except Exception as e:
            # Calcola durata
            duration = time.time() - start_time
            
            # Log dell'errore
            logger.error(
                "Request failed",
                method=method,
                url=url,
                error=str(e),
                duration=duration,
                event_name="request_failed",
                status="error"
            )
            
            # Log evento di sicurezza per errori 5xx
            if hasattr(e, 'status_code') and e.status_code >= 500:
                log_security_event(
                    event="server_error",
                    status="error",
                    endpoint=url,
                    reason=str(e),
                    ip_address=client_ip
                )
            
            raise
        finally:
            # Pulisci il contesto
            clear_context()
    
    async def _log_specific_operations(self, request: Request, response: Response, duration: float):
        """Logga operazioni specifiche basate sull'endpoint."""
        url = str(request.url.path)
        method = request.method
        status_code = response.status_code
        
        # Autenticazione
        if "/auth/" in url:
            if "login" in url:
                log_operation(
                    operation="user_login",
                    status="success" if status_code == 200 else "failed",
                    metadata={"endpoint": url}
                )
            elif "refresh" in url:
                log_operation(
                    operation="token_refresh",
                    status="success" if status_code == 200 else "failed",
                    metadata={"endpoint": url}
                )
        
        # Operazioni sui documenti
        elif "/documents/" in url:
            if method == "POST" and "upload" in url:
                log_operation(
                    operation="document_upload",
                    status="success" if status_code == 200 else "failed",
                    metadata={"endpoint": url}
                )
            elif method == "GET" and "download" in url:
                log_operation(
                    operation="document_download",
                    status="success" if status_code == 200 else "failed",
                    metadata={"endpoint": url}
                )
            elif method == "DELETE":
                log_operation(
                    operation="document_delete",
                    status="success" if status_code == 200 else "failed",
                    metadata={"endpoint": url}
                )
        
        # Operazioni BIM
        elif "/bim/" in url:
            log_operation(
                operation="bim_operation",
                status="success" if status_code == 200 else "failed",
                metadata={"endpoint": url}
            )
        
        # Operazioni AI
        elif "/ai/" in url:
            log_operation(
                operation="ai_interaction",
                status="success" if status_code == 200 else "failed",
                metadata={"endpoint": url}
            )
        
        # Operazioni attivatori
        elif "/activator/" in url:
            log_operation(
                operation="activator_control",
                status="success" if status_code == 200 else "failed",
                metadata={"endpoint": url}
            )
        
        # Operazioni voice
        elif "/voice/" in url:
            log_operation(
                operation="voice_command",
                status="success" if status_code == 200 else "failed",
                metadata={"endpoint": url}
            )
        
        # Log eventi di sicurezza per errori 4xx
        if 400 <= status_code < 500:
            log_security_event(
                event="client_error",
                status="failed",
                endpoint=url,
                reason=f"HTTP {status_code}",
                ip_address=request.client.host if request.client else "unknown"
            )


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
                "event_name": "unhandled_exception",
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


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware per logging specifico degli eventi di sicurezza.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Estrai informazioni di sicurezza
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Controlla header sospetti
        suspicious_headers = self._check_suspicious_headers(request)
        if suspicious_headers:
            log_security_event(
                event="suspicious_headers",
                status="warning",
                endpoint=str(request.url.path),
                reason=f"Suspicious headers detected: {suspicious_headers}",
                ip_address=client_ip,
                metadata={"user_agent": user_agent}
            )
        
        # Controlla rate limiting (se implementato)
        # TODO: Integrare con il sistema di rate limiting esistente
        
        response = await call_next(request)
        
        # Log accessi negati
        if response.status_code == 403:
            log_security_event(
                event="access_denied",
                status="denied",
                endpoint=str(request.url.path),
                reason="Forbidden access",
                ip_address=client_ip,
                metadata={"user_agent": user_agent}
            )
        elif response.status_code == 401:
            log_security_event(
                event="authentication_failed",
                status="failed",
                endpoint=str(request.url.path),
                reason="Authentication required",
                ip_address=client_ip,
                metadata={"user_agent": user_agent}
            )
        
        return response
    
    def _check_suspicious_headers(self, request: Request) -> list:
        """Controlla header sospetti nella request."""
        suspicious = []
        
        # Header che potrebbero indicare attacchi
        suspicious_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-forwarded-host",
            "x-forwarded-proto",
            "x-original-url",
            "x-rewrite-url"
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                suspicious.append(header)
        
        return suspicious 