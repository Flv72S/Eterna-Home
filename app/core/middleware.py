"""
Middleware per il logging delle richieste API con Trace ID.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger, set_trace_id, clear_trace_id

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware per il logging delle richieste API."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Genera Trace ID per la richiesta
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)
        
        # Log della richiesta in arrivo
        start_time = time.time()
        
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
            
            # Log della risposta
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
            
            # Log dell'errore
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
            # Pulisci il Trace ID
            clear_trace_id()


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware per il logging degli errori non gestiti."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error("Unhandled exception in request",
                         method=request.method,
                         path=request.url.path,
                         error=str(e),
                         error_type=type(e).__name__,
                         trace_id=getattr(request.state, 'trace_id', None),
                         exc_info=True)
            raise 