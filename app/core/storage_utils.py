"""
Utility per la gestione dello storage multi-tenant su MinIO.
Gestisce path dinamici basati su tenant_id per isolamento completo dei file.
"""

import uuid
import re
import logging
from typing import Optional, List
from pathlib import Path
import mimetypes
from datetime import datetime, timezone
from app.core.logging_multi_tenant import multi_tenant_logger

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file per sicurezza.
    Rimuove caratteri pericolosi, blocca path traversal e normalizza il nome.
    
    Args:
        filename: Nome del file originale
    
    Returns:
        str: Nome del file sanitizzato
        
    Raises:
        ValueError: Se il nome file contiene tentativi di path traversal
    """
    import unicodedata
    
    # Log del tentativo di sanitizzazione
    logger.info(f"Sanitizzazione nome file: {filename}")
    
    # Verifica path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        multi_tenant_logger.log_security_event(
            "path_traversal_attempt",
            {
                "filename": filename,
                "reason": "Path traversal detected",
                "event_type": "security_violation"
            }
        )
        logger.warning(f"Tentativo di path traversal rilevato: {filename}")
        raise ValueError("Nome file contiene caratteri non validi per path traversal")
    
    # Normalizza caratteri Unicode
    filename = unicodedata.normalize('NFKD', filename)
    
    # Rimuove caratteri pericolosi e non ASCII
    filename = re.sub(r'[^\w\s\-_.]', '', filename)
    
    # Sostituisce spazi con underscore
    filename = re.sub(r'\s+', '_', filename)
    
    # Rimuove caratteri duplicati
    filename = re.sub(r'_+', '_', filename)
    filename = re.sub(r'-+', '-', filename)
    
    # Rimuove underscore e trattini iniziali/finali
    filename = filename.strip('_-')
    
    # Se il nome è vuoto, genera un nome di default
    if not filename:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"file_{timestamp}"
    
    # Log del risultato
    logger.info(f"Nome file sanitizzato: {filename}")
    
    return filename

def get_tenant_storage_path(folder: str, tenant_id: uuid.UUID, filename: str) -> str:
    """
    Genera un path dinamico per lo storage multi-tenant.
    
    Args:
        folder: Cartella specifica (documents, bim, media, etc.)
        tenant_id: ID del tenant per isolamento
        filename: Nome del file da salvare
    
    Returns:
        str: Path completo per lo storage su MinIO
        
    Example:
        >>> get_tenant_storage_path("documents", uuid.uuid4(), "report.pdf")
        "tenants/123e4567-e89b-12d3-a456-426614174000/documents/2024_06_29__report_UUID.pdf"
    """
    # Sanitizza il nome del file per sicurezza
    safe_filename = sanitize_filename(filename)
    
    # Genera UUID univoco per evitare collisioni
    file_uuid = str(uuid.uuid4())[:8]
    
    # Aggiungi timestamp per tracciabilità
    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    
    # Estrai nome e estensione
    path = Path(safe_filename)
    name = path.stem
    extension = path.suffix
    
    # Costruisci nome file con timestamp e UUID
    unique_filename = f"{timestamp}__{name}_{file_uuid}{extension}"
    
    # Costruisce il path con struttura: tenants/{tenant_id}/{folder}/{filename}
    path = f"tenants/{tenant_id}/{folder}/{unique_filename}"
    
    return path

def get_tenant_folder_path(folder: str, tenant_id: uuid.UUID) -> str:
    """
    Genera il path della cartella per un tenant specifico.
    
    Args:
        folder: Cartella specifica (documents, bim, media, etc.)
        tenant_id: ID del tenant
    
    Returns:
        str: Path della cartella tenant
        
    Example:
        >>> get_tenant_folder_path("documents", uuid.uuid4())
        "tenants/123e4567-e89b-12d3-a456-426614174000/documents/"
    """
    return f"tenants/{tenant_id}/{folder}/"

def validate_path_security(path: str) -> bool:
    """
    Valida la sicurezza di un path per prevenire attacchi.
    
    Args:
        path: Path da validare
    
    Returns:
        bool: True se il path è sicuro, False altrimenti
    """
    # Verifica path traversal
    if '..' in path or '//' in path or '\\' in path:
        multi_tenant_logger.log_security_event(
            "path_traversal_attempt",
            {
                "path": path,
                "reason": "Path traversal detected in path validation",
                "event_type": "security_violation"
            }
        )
        logger.warning(f"Path traversal rilevato in validazione: {path}")
        return False
    
    # Verifica caratteri pericolosi
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in path:
            multi_tenant_logger.log_security_event(
                "dangerous_char_in_path",
                {
                    "path": path,
                    "char": char,
                    "reason": "Dangerous character in path",
                    "event_type": "security_violation"
                }
            )
            logger.warning(f"Carattere pericoloso rilevato in path: {char} in {path}")
            return False
    
    return True

def get_file_extension(filename: str) -> str:
    """
    Estrae l'estensione del file.
    
    Args:
        filename: Nome del file
    
    Returns:
        str: Estensione del file (senza punto)
    """
    return Path(filename).suffix.lower().lstrip('.')

def get_mime_type(filename: str) -> str:
    """
    Determina il MIME type del file basato sull'estensione.
    
    Args:
        filename: Nome del file
    
    Returns:
        str: MIME type del file
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Valida se il tipo di file è consentito.
    
    Args:
        filename: Nome del file da validare
        allowed_extensions: Lista delle estensioni consentite
    
    Returns:
        bool: True se il file è valido, False altrimenti
    """
    file_extension = get_file_extension(filename)
    is_valid = file_extension.lower() in [ext.lower() for ext in allowed_extensions]
    
    if not is_valid:
        multi_tenant_logger.log_security_event(
            "invalid_file_type",
            {
                "filename": filename,
                "extension": file_extension,
                "allowed_extensions": allowed_extensions,
                "reason": "File type not allowed",
                "event_type": "security_violation"
            }
        )
        logger.warning(f"Tipo file non consentito: {filename} (estensione: {file_extension})")
    
    return is_valid

def generate_unique_filename(original_filename: str, tenant_id: uuid.UUID) -> str:
    """
    Genera un nome file unico per evitare conflitti.
    Include timestamp, tenant_id e UUID per massima unicità.
    
    Args:
        original_filename: Nome del file originale
        tenant_id: ID del tenant
    
    Returns:
        str: Nome file unico con formato: YYYY_MM_DD__nome_UUID.ext
    """
    # Estrae nome e estensione
    path = Path(original_filename)
    name = path.stem
    extension = path.suffix
    
    # Sanitizza il nome
    safe_name = sanitize_filename(name)
    
    # Aggiunge timestamp, tenant_id e UUID per unicità
    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    tenant_short = str(tenant_id)[:8]  # Primi 8 caratteri del tenant_id
    file_uuid = str(uuid.uuid4())[:8]  # UUID univoco
    
    return f"{timestamp}__{safe_name}_{tenant_short}_{file_uuid}{extension}"

def parse_tenant_from_path(path: str) -> Optional[uuid.UUID]:
    """
    Estrae il tenant_id da un path di storage.
    
    Args:
        path: Path del file su MinIO
    
    Returns:
        Optional[uuid.UUID]: ID del tenant se valido, None altrimenti
    """
    try:
        # Path structure: tenants/{tenant_id}/{folder}/{filename}
        parts = path.split('/')
        if len(parts) >= 3 and parts[0] == 'tenants':
            return uuid.UUID(parts[1])
    except (ValueError, IndexError):
        pass
    
    return None

def is_valid_tenant_path(path: str, tenant_id: uuid.UUID) -> bool:
    """
    Verifica se un path appartiene al tenant specificato.
    
    Args:
        path: Path del file su MinIO
        tenant_id: ID del tenant da verificare
    
    Returns:
        bool: True se il path appartiene al tenant, False altrimenti
    """
    # Prima valida la sicurezza del path
    if not validate_path_security(path):
        return False
    
    path_tenant_id = parse_tenant_from_path(path)
    is_valid = path_tenant_id == tenant_id
    
    if not is_valid:
        multi_tenant_logger.log_security_event(
            "unauthorized_path_access",
            {
                "path": path,
                "requested_tenant": str(tenant_id),
                "path_tenant": str(path_tenant_id) if path_tenant_id else "None",
                "reason": "Path does not belong to tenant",
                "event_type": "security_violation"
            }
        )
        logger.warning(f"Tentativo di accesso non autorizzato al path: {path} (tenant: {tenant_id})")
    
    return is_valid

def get_storage_metrics_path(tenant_id: uuid.UUID) -> str:
    """
    Genera il path per le metriche di storage del tenant.
    
    Args:
        tenant_id: ID del tenant
    
    Returns:
        str: Path per le metriche
    """
    return f"tenants/{tenant_id}/metrics/"

def get_backup_path(tenant_id: uuid.UUID, backup_type: str = "daily") -> str:
    """
    Genera il path per i backup del tenant.
    
    Args:
        tenant_id: ID del tenant
        backup_type: Tipo di backup (daily, weekly, monthly)
    
    Returns:
        str: Path per i backup
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"tenants/{tenant_id}/backups/{backup_type}_{timestamp}/"

# Costanti per le cartelle supportate
SUPPORTED_FOLDERS = {
    "documents": "Documenti generici (PDF, DOC, etc.)",
    "bim": "Modelli BIM (IFC, GLTF, etc.)",
    "media": "File multimediali (audio, video, immagini)",
    "logs": "File di log e audit",
    "temp": "File temporanei",
    "backups": "Backup e archivi",
    "exports": "Esportazioni e report"
}

# Estensioni consentite per tipo di file
ALLOWED_EXTENSIONS = {
    "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
    "bim": [".ifc", ".gltf", ".glb", ".rvt", ".dwg", ".dxf"],
    "media": [".jpg", ".jpeg", ".png", ".gif", ".mp3", ".wav", ".mp4", ".avi"],
    "logs": [".log", ".txt", ".csv", ".json"],
    "temp": [".tmp", ".temp"],
    "backups": [".zip", ".tar", ".gz", ".7z"],
    "exports": [".csv", ".xlsx", ".json", ".xml", ".pdf"]
}

def get_allowed_extensions_for_folder(folder: str) -> List[str]:
    """
    Ottiene le estensioni consentite per una cartella specifica.
    
    Args:
        folder: Nome della cartella
    
    Returns:
        List[str]: Lista delle estensioni consentite
    """
    return ALLOWED_EXTENSIONS.get(folder, [])

def validate_folder(folder: str) -> bool:
    """
    Verifica se una cartella è supportata.
    
    Args:
        folder: Nome della cartella
    
    Returns:
        bool: True se la cartella è supportata, False altrimenti
    """
    return folder in SUPPORTED_FOLDERS

def get_folder_description(folder: str) -> str:
    """
    Ottiene la descrizione di una cartella.
    
    Args:
        folder: Nome della cartella
    
    Returns:
        str: Descrizione della cartella
    """
    return SUPPORTED_FOLDERS.get(folder, "Cartella non supportata")

# TODO: Implementare migrazione per creare bucket e cartelle tenant
# TODO: Aggiungere validazione automatica dei path durante upload/download
# TODO: Implementare cleanup automatico dei file temporanei
# TODO: Aggiungere metriche di utilizzo storage per tenant 