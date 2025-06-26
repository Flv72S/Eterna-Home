"""
Utility per la gestione dello storage multi-tenant su MinIO.
Gestisce path dinamici basati su tenant_id per isolamento completo dei file.
"""

import uuid
from typing import Optional, List
from pathlib import Path
import mimetypes
from datetime import datetime, timezone

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
        "tenants/123e4567-e89b-12d3-a456-426614174000/documents/report.pdf"
    """
    # Sanitizza il nome del file per sicurezza
    safe_filename = sanitize_filename(filename)
    
    # Costruisce il path con struttura: tenants/{tenant_id}/{folder}/{filename}
    path = f"tenants/{tenant_id}/{folder}/{safe_filename}"
    
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

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file per sicurezza.
    Rimuove caratteri pericolosi e normalizza il nome.
    
    Args:
        filename: Nome del file originale
    
    Returns:
        str: Nome del file sanitizzato
    """
    import re
    import unicodedata
    
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
    
    return filename

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
    return file_extension.lower() in [ext.lower() for ext in allowed_extensions]

def generate_unique_filename(original_filename: str, tenant_id: uuid.UUID) -> str:
    """
    Genera un nome file unico per evitare conflitti.
    
    Args:
        original_filename: Nome del file originale
        tenant_id: ID del tenant
    
    Returns:
        str: Nome file unico
    """
    # Estrae nome e estensione
    path = Path(original_filename)
    name = path.stem
    extension = path.suffix
    
    # Sanitizza il nome
    safe_name = sanitize_filename(name)
    
    # Aggiunge timestamp e tenant_id per unicità
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = str(tenant_id)[:8]  # Primi 8 caratteri del tenant_id
    
    return f"{safe_name}_{timestamp}_{unique_id}{extension}"

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
    path_tenant_id = parse_tenant_from_path(path)
    return path_tenant_id == tenant_id

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