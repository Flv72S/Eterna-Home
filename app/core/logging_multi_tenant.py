"""
Sistema di logging multi-tenant con formato JSON.
Garantisce che ogni log includa il tenant_id quando disponibile.
"""

import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from contextvars import ContextVar
import uuid
import os
from pathlib import Path

# Context variable per il tenant_id corrente
current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar('current_tenant_id', default=None)
current_user_id: ContextVar[Optional[int]] = ContextVar('current_user_id', default=None)

class MultiTenantJSONFormatter(logging.Formatter):
    """
    Formatter JSON per log multi-tenant.
    Include automaticamente tenant_id e user_id quando disponibili.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatta il record di log in JSON con informazioni multi-tenant."""
        
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Aggiungi tenant_id se disponibile
        tenant_id = current_tenant_id.get()
        if tenant_id:
            log_entry["tenant_id"] = str(tenant_id)
        
        # Aggiungi user_id se disponibile
        user_id = current_user_id.get()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Aggiungi exception info se presente
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Aggiungi extra fields se presenti
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class MultiTenantLogger:
    """
    Logger centralizzato per il sistema multi-tenant.
    Gestisce il logging con isolamento per tenant.
    """
    
    def __init__(self, name: str = "eterna_home"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Evita duplicazione degli handler
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura gli handler per console e file."""
        
        # Formatter JSON
        formatter = MultiTenantJSONFormatter()
        
        # Handler per console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler per file generale
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler per errori
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "errors.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def _log_with_context(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log con contesto multi-tenant."""
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        
        if extra_fields:
            record.extra_fields = extra_fields
        
        self.logger.handle(record)
    
    def info(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log di livello INFO."""
        self._log_with_context(logging.INFO, message, extra_fields)
    
    def warning(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log di livello WARNING."""
        self._log_with_context(logging.WARNING, message, extra_fields)
    
    def error(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log di livello ERROR."""
        self._log_with_context(logging.ERROR, message, extra_fields)
    
    def critical(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log di livello CRITICAL."""
        self._log_with_context(logging.CRITICAL, message, extra_fields)
    
    def debug(self, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log di livello DEBUG."""
        self._log_with_context(logging.DEBUG, message, extra_fields)
    
    def log_event(self, event: str, metadata: Optional[Dict[str, Any]] = None):
        """Log di un evento specifico con metadati."""
        extra_fields = {
            "event": event,
            "metadata": metadata or {}
        }
        self.info(f"Event: {event}", extra_fields)
    
    def log_security_event(self, event: str, metadata: Optional[Dict[str, Any]] = None):
        """Log di un evento di sicurezza."""
        extra_fields = {
            "event": event,
            "event_type": "security",
            "metadata": metadata or {}
        }
        self.warning(f"Security Event: {event}", extra_fields)
    
    def log_ai_interaction(self, prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None):
        """Log di un'interazione AI."""
        extra_fields = {
            "event": "ai_interaction",
            "event_type": "ai",
            "prompt_length": len(prompt),
            "response_length": len(response),
            "metadata": metadata or {}
        }
        self.info("AI Interaction", extra_fields)

# Logger globale
multi_tenant_logger = MultiTenantLogger()

def get_logger(name: str) -> MultiTenantLogger:
    """
    Restituisce un logger per il modulo specificato.
    Mantiene compatibilità con il logging standard.
    """
    return MultiTenantLogger(name)

def set_tenant_context(tenant_id: Optional[uuid.UUID] = None, user_id: Optional[int] = None):
    """
    Imposta il contesto del tenant per il logging.
    Da chiamare all'inizio di ogni request.
    """
    if tenant_id:
        current_tenant_id.set(tenant_id)
    if user_id:
        current_user_id.set(user_id)

def clear_tenant_context():
    """Pulisce il contesto del tenant."""
    current_tenant_id.set(None)
    current_user_id.set(None)

def log_with_tenant(tenant_id: uuid.UUID, user_id: int, message: str, extra_fields: Optional[Dict[str, Any]] = None):
    """Log con contesto tenant temporaneo."""
    with TenantContext(tenant_id, user_id):
        multi_tenant_logger.info(message, extra_fields)

class TenantContext:
    """
    Context manager per il logging con contesto tenant.
    """
    
    def __init__(self, tenant_id: Optional[uuid.UUID] = None, user_id: Optional[int] = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.old_tenant_id = None
        self.old_user_id = None
    
    def __enter__(self):
        """Imposta il contesto del tenant."""
        self.old_tenant_id = current_tenant_id.get()
        self.old_user_id = current_user_id.get()
        
        if self.tenant_id:
            current_tenant_id.set(self.tenant_id)
        if self.user_id:
            current_user_id.set(self.user_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ripristina il contesto precedente."""
        current_tenant_id.set(self.old_tenant_id)
        current_user_id.set(self.old_user_id)

# Funzioni di utilità per logging specifico
def log_user_login(user_id: int, tenant_id: uuid.UUID, success: bool, ip_address: Optional[str] = None):
    """Log di login utente."""
    extra_fields = {
        "event": "user_login",
        "event_type": "authentication",
        "success": success,
        "ip_address": ip_address
    }
    log_with_tenant(tenant_id, user_id, f"User login {'successful' if success else 'failed'}", extra_fields)

def log_document_operation(operation: str, document_id: int, user_id: int, tenant_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None):
    """Log di operazioni sui documenti."""
    extra_fields = {
        "event": f"document_{operation}",
        "event_type": "document",
        "document_id": document_id,
        "metadata": metadata or {}
    }
    log_with_tenant(tenant_id, user_id, f"Document {operation}", extra_fields)

def log_ai_usage(user_id: int, tenant_id: uuid.UUID, prompt_tokens: int, response_tokens: int, metadata: Optional[Dict[str, Any]] = None):
    """Log di utilizzo AI."""
    extra_fields = {
        "event": "ai_usage",
        "event_type": "ai",
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "total_tokens": prompt_tokens + response_tokens,
        "metadata": metadata or {}
    }
    log_with_tenant(tenant_id, user_id, "AI usage", extra_fields)

def log_security_violation(user_id: Optional[int], tenant_id: Optional[uuid.UUID], violation_type: str, details: str):
    """Log di violazioni di sicurezza."""
    extra_fields = {
        "event": "security_violation",
        "event_type": "security",
        "violation_type": violation_type,
        "details": details
    }
    
    if tenant_id and user_id:
        log_with_tenant(tenant_id, user_id, f"Security violation: {violation_type}", extra_fields)
    else:
        multi_tenant_logger.log_security_event(f"Security violation: {violation_type}", extra_fields) 