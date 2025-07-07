"""
Configurazione del sistema di logging strutturato per Eterna Home.
Utilizza structlog per produrre log in formato JSON compatibili con ELK/Grafana Loki.
"""
import sys
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

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

# Context variable per il Trace ID
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    """Ottiene il Trace ID corrente o ne genera uno nuovo."""
    trace_id = trace_id_var.get()
    if trace_id is None:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
    return trace_id


def add_trace_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge il Trace ID al log."""
    event_dict["trace_id"] = get_trace_id()
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge timestamp ISO al log."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge informazioni del servizio al log."""
    event_dict["service"] = "eterna-home-api"
    event_dict["version"] = "1.0.0"
    return event_dict


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    include_trace_id: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configura il sistema di logging strutturato.
    
    Args:
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Se True, usa formato JSON, altrimenti testo
        include_trace_id: Se True, include Trace ID nei log
        log_file: Percorso del file di log (opzionale)
    """
    # Configura i processori structlog
    processors: list[Processor] = [
        UnicodeDecoder(),
        add_log_level,
        StackInfoRenderer(),
        format_exc_info,
        TimeStamper(fmt="iso"),
        add_timestamp,
        add_service_info,
    ]
    
    if include_trace_id:
        processors.append(add_trace_id)
    
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
    
    # Se specificato un file di log, aggiungi un handler per file
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Ottiene un logger strutturato.
    
    Args:
        name: Nome del logger (solitamente __name__)
    
    Returns:
        Logger strutturato configurato
    """
    return structlog.get_logger(name)


def set_trace_id(trace_id: str) -> None:
    """
    Imposta il Trace ID per il contesto corrente.
    
    Args:
        trace_id: ID del trace da utilizzare
    """
    trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """Pulisce il Trace ID dal contesto corrente."""
    trace_id_var.set(None)


# Configurazione di default
setup_logging(
    level="INFO",
    json_format=True,
    include_trace_id=True
)

# Logger di default per il modulo
logger = get_logger(__name__) 