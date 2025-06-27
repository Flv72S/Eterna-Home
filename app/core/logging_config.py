"""
Configurazione centralizzata del sistema di logging per Eterna Home.
Integra structlog con sistema multi-tenant per log strutturati JSON.
Compatibile con Grafana Loki, ELK Stack e altri log collectors.
"""

import sys
import logging
import logging.handlers
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from pathlib import Path
import os

import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import (
    TimeStamper,
    JSONRenderer,
    add_log_level,
    StackInfoRenderer,
    format_exc_info,
    UnicodeDecoder,
)
from structlog.types import Processor

# Context variables per il contesto multi-tenant
current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar('current_tenant_id', default=None)
current_user_id: ContextVar[Optional[int]] = ContextVar('current_user_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

def get_trace_id() -> str:
    """Ottiene il Trace ID corrente o ne genera uno nuovo."""
    trace_id = trace_id_var.get()
    if trace_id is None:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
    return trace_id

def get_request_id() -> str:
    """Ottiene il Request ID corrente o ne genera uno nuovo."""
    request_id = request_id_var.get()
    if request_id is None:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
    return request_id

def add_context_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge informazioni di contesto al log."""
    # Trace ID
    event_dict["trace_id"] = get_trace_id()
    
    # Request ID
    event_dict["request_id"] = get_request_id()
    
    # Tenant ID
    tenant_id = current_tenant_id.get()
    if tenant_id:
        event_dict["tenant_id"] = str(tenant_id)
    
    # User ID
    user_id = current_user_id.get()
    if user_id:
        event_dict["user_id"] = user_id
    
    # Timestamp ISO
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Service info
    event_dict["service"] = "eterna-home-api"
    event_dict["version"] = "1.0.0"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    
    return event_dict

def add_event_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge informazioni sull'evento al log."""
    # Determina il tipo di evento basato sul messaggio
    message = event_dict.get("event", "")
    
    if "login" in message.lower():
        event_dict["event_type"] = "authentication"
    elif "upload" in message.lower():
        event_dict["event_type"] = "file_operation"
    elif "download" in message.lower():
        event_dict["event_type"] = "file_operation"
    elif "delete" in message.lower():
        event_dict["event_type"] = "file_operation"
    elif "security" in message.lower() or "violation" in message.lower():
        event_dict["event_type"] = "security"
    elif "ai" in message.lower():
        event_dict["event_type"] = "ai_interaction"
    elif "activator" in message.lower():
        event_dict["event_type"] = "device_control"
    else:
        event_dict["event_type"] = "general"
    
    return event_dict

def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configura il sistema di logging strutturato.
    
    Args:
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Se True, usa formato JSON, altrimenti testo
        log_dir: Directory per i file di log
        max_file_size: Dimensione massima file di log
        backup_count: Numero di backup da mantenere
    """
    # Crea directory logs se non esiste
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configura i processori structlog
    processors: list[Processor] = [
        UnicodeDecoder(),
        add_log_level,
        StackInfoRenderer(),
        format_exc_info,
        TimeStamper(fmt="iso"),
        add_context_info,
        add_event_info,
    ]
    
    if json_format:
        processors.append(JSONRenderer())
    else:
        # Formato testo per sviluppo locale
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    
    # Configura structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configura il logging standard
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Handler per file generale
    general_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.json",
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    general_handler.setLevel(getattr(logging, level.upper()))
    logging.getLogger().addHandler(general_handler)
    
    # Handler per errori
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.json",
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(error_handler)
    
    # Handler per eventi di sicurezza
    security_handler = logging.handlers.RotatingFileHandler(
        log_path / "security.json",
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    security_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(security_handler)

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Ottiene un logger strutturato.
    
    Args:
        name: Nome del logger (solitamente __name__)
    
    Returns:
        Logger strutturato configurato
    """
    return structlog.get_logger(name)

def set_context(
    tenant_id: Optional[uuid.UUID] = None,
    user_id: Optional[int] = None,
    trace_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Imposta il contesto per il logging.
    
    Args:
        tenant_id: ID del tenant
        user_id: ID dell'utente
        trace_id: ID del trace
        request_id: ID della request
    """
    if tenant_id:
        current_tenant_id.set(tenant_id)
    if user_id:
        current_user_id.set(user_id)
    if trace_id:
        trace_id_var.set(trace_id)
    if request_id:
        request_id_var.set(request_id)

def clear_context() -> None:
    """Pulisce il contesto corrente."""
    current_tenant_id.set(None)
    current_user_id.set(None)
    trace_id_var.set(None)
    request_id_var.set(None)

def log_security_event(
    event: str,
    status: str = "failed",
    user_id: Optional[int] = None,
    tenant_id: Optional[uuid.UUID] = None,
    endpoint: Optional[str] = None,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Utility per loggare eventi di sicurezza.
    
    Args:
        event: Tipo di evento (es. "access_denied", "upload_blocked", "rbac_violation")
        status: Status dell'evento (success, failed, unauthorized, blocked)
        user_id: ID dell'utente
        tenant_id: ID del tenant
        endpoint: Endpoint chiamato
        reason: Motivo del blocco/errore
        ip_address: Indirizzo IP
        metadata: Metadati aggiuntivi
    """
    logger = get_logger("security")
    
    log_data = {
        "security_event": event,
        "status": status,
        "event_type": "security",
        "level": "WARNING" if status in ["failed", "unauthorized", "blocked"] else "INFO"
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if tenant_id:
        log_data["tenant_id"] = str(tenant_id)
    if endpoint:
        log_data["endpoint"] = endpoint
    if reason:
        log_data["reason"] = reason
    if ip_address:
        log_data["ip_address"] = ip_address
    if metadata:
        log_data["metadata"] = metadata
    
    if status in ["failed", "unauthorized", "blocked"]:
        logger.warning(f"Security Event: {event}", **log_data)
    else:
        logger.info(f"Security Event: {event}", **log_data)

def log_operation(
    operation: str,
    status: str = "success",
    user_id: Optional[int] = None,
    tenant_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Utility per loggare operazioni generiche.
    
    Args:
        operation: Tipo di operazione (es. "upload_document", "delete_file", "login")
        status: Status dell'operazione (success, failed, unauthorized)
        user_id: ID dell'utente
        tenant_id: ID del tenant
        resource_type: Tipo di risorsa (document, file, user, etc.)
        resource_id: ID della risorsa
        metadata: Metadati aggiuntivi
    """
    logger = get_logger("operations")
    
    log_data = {
        "operation_type": operation,
        "status": status,
        "event_type": "operation"
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if tenant_id:
        log_data["tenant_id"] = str(tenant_id)
    if resource_type:
        log_data["resource_type"] = resource_type
    if resource_id:
        log_data["resource_id"] = resource_id
    if metadata:
        log_data["metadata"] = metadata
    
    if status == "success":
        logger.info(f"Operation: {operation}", **log_data)
    else:
        logger.warning(f"Operation Failed: {operation}", **log_data)

# Configurazione di default
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "json").lower() == "json",
    log_dir=os.getenv("LOG_DIR", "logs")
)

# Logger di default per il modulo
logger = get_logger(__name__) 