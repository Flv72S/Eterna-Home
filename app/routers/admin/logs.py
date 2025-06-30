"""
Router per la gestione amministrativa dei log strutturati.
Implementa visualizzazione log con filtri multi-tenant e protezione RBAC.
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import uuid

from app.core.auth import require_permission_in_tenant
from app.core.deps import get_current_tenant, get_db, get_current_user
from app.models.user import User
from app.models.user_tenant_role import UserTenantRole
from app.core.logging_config import get_logger

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates/admin")
logger = get_logger(__name__)

# Configurazione log files
LOG_DIR = "logs"
LOG_FILES = {
    "app": "app.json",
    "security": "security.json", 
    "errors": "errors.json"
}

# Eventi disponibili per i filtri
AVAILABLE_EVENTS = [
    "user_login",
    "user_logout", 
    "file_upload",
    "file_download",
    "ai_interaction",
    "security_violation",
    "access_denied",
    "role_assignment",
    "mfa_setup",
    "mfa_enable",
    "mfa_disable",
    "document_create",
    "document_update",
    "document_delete",
    "bim_upload",
    "bim_conversion",
    "voice_command",
    "system_error",
    "database_error",
    "api_error"
]

def read_log_file(file_path: str, max_lines: int = 1000) -> List[Dict[str, Any]]:
    """
    Legge un file di log JSON newline-delimited.
    
    Args:
        file_path: Percorso del file di log
        max_lines: Numero massimo di righe da leggere
        
    Returns:
        Lista di log entries parsati
    """
    logs = []
    
    if not os.path.exists(file_path):
        return logs
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Prendi solo le ultime max_lines righe
            lines = lines[-max_lines:] if len(lines) > max_lines else lines
            
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # Salta righe non valide
                        continue
                        
    except Exception as e:
        logger.error(f"Errore durante lettura log file {file_path}: {e}")
    
    return logs

def filter_logs_by_tenant(logs: List[Dict[str, Any]], tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Filtra i log per tenant_id.
    
    Args:
        logs: Lista di log entries
        tenant_id: ID del tenant
        
    Returns:
        Log filtrati per tenant
    """
    filtered_logs = []
    tenant_id_str = str(tenant_id)
    
    for log_entry in logs:
        # Controlla se il log ha tenant_id e corrisponde
        log_tenant_id = log_entry.get('tenant_id')
        if log_tenant_id == tenant_id_str:
            filtered_logs.append(log_entry)
    
    return filtered_logs

def apply_log_filters(
    logs: List[Dict[str, Any]], 
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Applica filtri ai log.
    
    Args:
        logs: Lista di log entries
        user_id: Filtro per user_id
        event_type: Filtro per event_type
        date_start: Data inizio (YYYY-MM-DD)
        date_end: Data fine (YYYY-MM-DD)
        
    Returns:
        Log filtrati
    """
    filtered_logs = logs
    
    # Filtro per user_id
    if user_id:
        filtered_logs = [
            log for log in filtered_logs 
            if log.get('user_id') == user_id
        ]
    
    # Filtro per event_type
    if event_type:
        filtered_logs = [
            log for log in filtered_logs 
            if log.get('event') == event_type
        ]
    
    # Filtro per data
    if date_start or date_end:
        filtered_logs = [
            log for log in filtered_logs
            if is_log_in_date_range(log, date_start, date_end)
        ]
    
    return filtered_logs

def is_log_in_date_range(log_entry: Dict[str, Any], date_start: Optional[str], date_end: Optional[str]) -> bool:
    """
    Verifica se un log entry è nel range di date specificato.
    
    Args:
        log_entry: Entry del log
        date_start: Data inizio (YYYY-MM-DD)
        date_end: Data fine (YYYY-MM-DD)
        
    Returns:
        True se il log è nel range
    """
    try:
        timestamp = log_entry.get('timestamp')
        if not timestamp:
            return False
        
        # Parsa il timestamp
        if isinstance(timestamp, str):
            log_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            log_date = datetime.fromtimestamp(timestamp)
        
        # Filtro data inizio
        if date_start:
            start_date = datetime.strptime(date_start, '%Y-%m-%d')
            if log_date.date() < start_date.date():
                return False
        
        # Filtro data fine
        if date_end:
            end_date = datetime.strptime(date_end, '%Y-%m-%d')
            if log_date.date() > end_date.date():
                return False
        
        return True
        
    except Exception:
        return False

def sanitize_log_entry(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizza un log entry rimuovendo informazioni sensibili.
    
    Args:
        log_entry: Entry del log originale
        
    Returns:
        Entry del log sanitizzato
    """
    sanitized = log_entry.copy()
    
    # Rimuovi campi sensibili
    sensitive_fields = [
        'password', 'token', 'secret', 'key', 'credential',
        'stacktrace', 'traceback', 'internal_error'
    ]
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '[REDACTED]'
    
    # Sanitizza messaggi che potrebbero contenere info sensibili
    if 'message' in sanitized:
        message = sanitized['message']
        # Rimuovi token JWT dal messaggio
        if 'Bearer ' in message:
            parts = message.split('Bearer ')
            if len(parts) > 1:
                sanitized['message'] = parts[0] + 'Bearer [REDACTED]'
    
    return sanitized

@router.get("/logs/{log_type}", response_class=None)
def admin_logs_view(
    request: Request,
    log_type: str,
    user_id: Optional[str] = Query(None, description="Filtro per user_id"),
    event_type: Optional[str] = Query(None, description="Filtro per event_type"),
    date_start: Optional[str] = Query(None, description="Data inizio (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="Data fine (YYYY-MM-DD)"),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("view_logs")),
    db: Session = Depends(get_db)
):
    """
    Visualizza i log del tipo specificato con filtri applicati.
    """
    # Verifica che il tipo di log sia valido
    if log_type not in LOG_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo di log '{log_type}' non valido"
        )
    
    # Percorso del file di log
    log_file_path = os.path.join(LOG_DIR, LOG_FILES[log_type])
    
    # Leggi i log dal file
    logs = read_log_file(log_file_path)
    
    # Filtra per tenant
    logs = filter_logs_by_tenant(logs, tenant_id)
    
    # Applica filtri aggiuntivi
    logs = apply_log_filters(logs, user_id, event_type, date_start, date_end)
    
    # Sanitizza i log
    logs = [sanitize_log_entry(log) for log in logs]
    
    # Ordina per timestamp (più recenti prima)
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Limita il numero di risultati per performance
    logs = logs[:1000]
    
    # Recupera utenti del tenant per il dropdown
    users_query = (
        select(User.id, User.username, User.email)
        .join(UserTenantRole, User.id == UserTenantRole.user_id)
        .where(UserTenantRole.tenant_id == tenant_id)
        .order_by(User.username)
    )
    users = db.exec(users_query).all()
    
    # Formatta i log per il template
    formatted_logs = []
    for log in logs:
        formatted_log = {
            'timestamp': log.get('timestamp', 'N/A'),
            'tenant_id': log.get('tenant_id', 'N/A'),
            'user_id': log.get('user_id', 'N/A'),
            'event': log.get('event', 'N/A'),
            'status': log.get('status', 'N/A'),
            'message': log.get('message', 'N/A'),
            'level': log.get('level', 'INFO'),
            'trace_id': log.get('trace_id', 'N/A')
        }
        formatted_logs.append(formatted_log)
    
    # Statistiche
    stats = {
        'total_logs': len(formatted_logs),
        'error_count': len([log for log in formatted_logs if log['level'] == 'ERROR']),
        'warning_count': len([log for log in formatted_logs if log['level'] == 'WARNING']),
        'info_count': len([log for log in formatted_logs if log['level'] == 'INFO'])
    }
    
    return templates.TemplateResponse("logs/viewer.html", {
        "request": request,
        "log_type": log_type,
        "logs": formatted_logs,
        "users": users,
        "available_events": AVAILABLE_EVENTS,
        "stats": stats,
        "filters": {
            "user_id": user_id,
            "event_type": event_type,
            "date_start": date_start,
            "date_end": date_end
        },
        "tenant_id": tenant_id
    })

@router.get("/logs", response_class=None)
def admin_logs_overview(
    request: Request,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("view_logs")),
    db: Session = Depends(get_db)
):
    """
    Overview dei log disponibili.
    """
    # Statistiche generali per ogni tipo di log
    log_stats = {}
    
    for log_type, filename in LOG_FILES.items():
        log_file_path = os.path.join(LOG_DIR, filename)
        logs = read_log_file(log_file_path, max_lines=10000)  # Leggi più righe per statistiche
        logs = filter_logs_by_tenant(logs, tenant_id)
        
        # Calcola statistiche
        total_count = len(logs)
        error_count = len([log for log in logs if log.get('level') == 'ERROR'])
        warning_count = len([log for log in logs if log.get('level') == 'WARNING'])
        info_count = len([log for log in logs if log.get('level') == 'INFO'])
        
        # Ultimi eventi
        recent_logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
        
        log_stats[log_type] = {
            'total': total_count,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'recent_logs': recent_logs
        }
    
    return templates.TemplateResponse("logs/overview.html", {
        "request": request,
        "log_stats": log_stats,
        "tenant_id": tenant_id
    })

@router.get("/logs/export/{log_type}")
def admin_logs_export(
    log_type: str,
    format: str = Query("json", description="Formato export (json, csv)"),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("view_logs")),
    db: Session = Depends(get_db)
):
    """
    Esporta i log in formato JSON o CSV.
    """
    # Verifica che il tipo di log sia valido
    if log_type not in LOG_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo di log '{log_type}' non valido"
        )
    
    # Percorso del file di log
    log_file_path = os.path.join(LOG_DIR, LOG_FILES[log_type])
    
    # Leggi e filtra i log
    logs = read_log_file(log_file_path)
    logs = filter_logs_by_tenant(logs, tenant_id)
    logs = [sanitize_log_entry(log) for log in logs]
    
    # Ordina per timestamp
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    if format.lower() == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        if logs:
            writer.writerow(logs[0].keys())
        
        # Dati
        for log in logs:
            writer.writerow(log.values())
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={log_type}_logs.csv"}
        )
    
    else:  # JSON
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=logs,
            headers={"Content-Disposition": f"attachment; filename={log_type}_logs.json"}
        ) 