"""
Sistema di validazione avanzata per Eterna Home.
Gestisce sanificazione file, validazione MIME types e protezione contro input malevoli.
"""

import re
import mimetypes
import os
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from pydantic import validator, ValidationError
import logging
from app.core.logging_multi_tenant import multi_tenant_logger

logger = logging.getLogger(__name__)

# Configurazioni di sicurezza
ALLOWED_MIME_TYPES = {
    # Documenti
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.ms-excel": [".xls"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    
    # Immagini
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    "image/svg+xml": [".svg"],
    
    # Modelli BIM
    "application/octet-stream": [".ifc", ".rvt", ".dwg", ".dxf"],  # BIM files
    "model/ifc": [".ifc"],
    "application/ifc": [".ifc"],
    
    # Audio
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/mp4": [".m4a"],
    "audio/flac": [".flac"],
    "audio/ogg": [".ogg"],
    
    # Video (se necessario)
    "video/mp4": [".mp4"],
    "video/webm": [".webm"],
    
    # Archivi
    "application/zip": [".zip"],
    "application/x-rar-compressed": [".rar"],
    "application/x-7z-compressed": [".7z"]
}

# Limiti di dimensione file (in bytes)
FILE_SIZE_LIMITS = {
    "document": 50 * 1024 * 1024,  # 50MB
    "image": 10 * 1024 * 1024,     # 10MB
    "bim": 500 * 1024 * 1024,      # 500MB
    "audio": 100 * 1024 * 1024,    # 100MB
    "video": 200 * 1024 * 1024,    # 200MB
    "archive": 100 * 1024 * 1024   # 100MB
}

# Regex per validazione campi testo
TEXT_FIELD_REGEX = {
    "title": r"^[a-zA-Z0-9\s\-_.,!?()]+$",
    "description": r"^[a-zA-Z0-9\s\-_.,!?()@#$%&*+=:;<>\"'[\]{}|\\/]+$",
    "filename": r"^[a-zA-Z0-9\s\-_.]+$",
    "path": r"^[a-zA-Z0-9\s\-_./]+$",
    "change_description": r"^[a-zA-Z0-9\s\-_.,!?()@#$%&*+=:;<>\"'[\]{}|\\/]+$"
}

# MIME types vietati (eseguibili, script, etc.)
FORBIDDEN_MIME_TYPES = {
    "application/x-msdownload",  # .exe
    "application/x-executable",
    "application/x-msi",
    "application/x-msdos-program",
    "application/x-bat",
    "application/x-com",
    "text/x-python",
    "application/x-python-code",
    "text/x-script",
    "application/x-shellscript",
    "text/x-shellscript",
    "application/x-javascript",
    "text/javascript",
    "application/x-php",
    "text/x-php"
}

class FileValidator:
    """Validatore per file upload con protezione avanzata."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanifica il nome del file rimuovendo caratteri pericolosi.
        
        Args:
            filename: Nome file originale
            
        Returns:
            str: Nome file sanificato
            
        Raises:
            HTTPException: Se il nome file non è valido
        """
        if not filename:
            FileValidator._log_invalid_filename(filename, "Nome file vuoto")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nome file non può essere vuoto"
            )
        
        # Rimuovi path traversal
        filename = os.path.basename(filename)
        
        # Verifica path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            FileValidator._log_invalid_filename(filename, "Path traversal rilevato")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nome file contiene caratteri non validi per path traversal"
            )
        
        # Rimuovi caratteri pericolosi
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Rimuovi spazi multipli e caratteri di controllo
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        
        # Limita lunghezza
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Assicurati che non sia vuoto dopo la sanificazione
        if not filename or filename == '.' or filename == '..':
            FileValidator._log_invalid_filename(filename, "Nome file non valido dopo sanificazione")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nome file non valido dopo sanificazione"
            )
        
        return filename
    
    @staticmethod
    def is_allowed_mime_type(mime_type: str, filename: str) -> bool:
        """
        Verifica se il MIME type è consentito per il file.
        
        Args:
            mime_type: MIME type del file
            filename: Nome del file
            
        Returns:
            bool: True se consentito, False altrimenti
        """
        if not mime_type or not filename:
            return False
        
        # Verifica MIME types vietati
        if mime_type in FORBIDDEN_MIME_TYPES:
            return False
        
        # Ottieni estensione
        _, ext = os.path.splitext(filename.lower())
        
        # Verifica estensioni vietate
        forbidden_extensions = ['.exe', '.bat', '.com', '.cmd', '.scr', '.pif', '.vbs', '.js', '.jar', '.msi']
        if ext in forbidden_extensions:
            return False
        
        # Verifica se il MIME type è nella whitelist
        if mime_type not in ALLOWED_MIME_TYPES:
            return False
        
        # Verifica che l'estensione corrisponda al MIME type
        allowed_extensions = ALLOWED_MIME_TYPES[mime_type]
        return ext in allowed_extensions
    
    @staticmethod
    def get_file_category(mime_type: str) -> str:
        """
        Determina la categoria del file basata sul MIME type.
        
        Args:
            mime_type: MIME type del file
            
        Returns:
            str: Categoria del file
        """
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type in ["application/zip", "application/x-rar-compressed", "application/x-7z-compressed"]:
            return "archive"
        elif mime_type in ["application/octet-stream", "model/ifc", "application/ifc"]:
            return "bim"
        else:
            return "document"
    
    @staticmethod
    def validate_file_upload(
        file: UploadFile, 
        allowed_types: List[str],
        max_size: int
    ) -> None:
        """
        Valida un file upload completo secondo i requisiti specifici.
        
        Args:
            file: File da validare
            allowed_types: Lista di MIME types consentiti
            max_size: Dimensione massima in bytes
            
        Raises:
            HTTPException: Se il file non è valido
        """
        try:
            # Sanifica nome file
            safe_filename = FileValidator.sanitize_filename(file.filename)
            
            # Verifica MIME type
            if not FileValidator.is_allowed_mime_type(file.content_type, safe_filename):
                FileValidator._log_invalid_upload(file, "MIME type non consentito")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Tipo di file non consentito: {file.content_type}"
                )
            
            # Verifica che il MIME type sia nella lista consentita
            if file.content_type not in allowed_types:
                FileValidator._log_invalid_upload(file, f"MIME type non nella lista consentita: {file.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Tipo di file non consentito per questo endpoint: {file.content_type}"
                )
            
            # Leggi il file per verificare la dimensione
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            if len(content) > max_size:
                FileValidator._log_invalid_upload(file, f"File troppo grande: {len(content)} > {max_size}")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File troppo grande. Massimo consentito: {max_size // (1024*1024)}MB"
                )
            
            # Log upload valido
            FileValidator._log_valid_upload(file, safe_filename, len(content))
            
        except HTTPException:
            raise
        except Exception as e:
            FileValidator._log_invalid_upload(file, f"Errore validazione: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Errore nella validazione del file"
            )
    
    @staticmethod
    def _log_invalid_filename(filename: str, reason: str):
        """Logga un nome file non valido."""
        multi_tenant_logger.log_security_event(
            "invalid_filename",
            {
                "filename": filename,
                "reason": reason
            }
        )
        
        logger.warning(
            f"Invalid filename rejected: {filename}",
            extra={
                "filename": filename,
                "reason": reason,
                "event_type": "invalid_filename"
            }
        )
    
    @staticmethod
    def _log_invalid_upload(file: UploadFile, reason: str):
        """Logga un upload non valido."""
        multi_tenant_logger.log_security_event(
            "invalid_file_upload",
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "reason": reason,
                "file_size": getattr(file, 'size', 'unknown')
            }
        )
        
        logger.warning(
            f"Invalid file upload rejected: {file.filename}",
            extra={
                "uploaded_filename": file.filename,
                "content_type": file.content_type,
                "reason": reason,
                "event_type": "invalid_file_upload"
            }
        )
    
    @staticmethod
    def _log_valid_upload(file: UploadFile, safe_filename: str, size: int):
        """Logga un upload valido."""
        multi_tenant_logger.info(
            f"File upload validated: {safe_filename}",
            {
                "original_filename": file.filename,
                "safe_filename": safe_filename,
                "content_type": file.content_type,
                "size": size,
                "event_type": "valid_file_upload"
            }
        )

class TextValidator:
    """Validatore per campi testo con protezione contro injection."""
    
    @staticmethod
    def validate_text_field(
        value: str, 
        field_name: str, 
        max_length: int = 1000,
        regex: str = None
    ) -> str:
        """
        Valida un campo testo secondo i requisiti specifici.
        
        Args:
            value: Valore da validare
            field_name: Nome del campo per logging
            max_length: Lunghezza massima
            regex: Regex pattern per validazione (se None usa quello di default)
            
        Returns:
            str: Valore validato
            
        Raises:
            HTTPException: Se il valore non è valido
        """
        if not value:
            return value
        
        # Verifica lunghezza
        if len(value) > max_length:
            TextValidator._log_invalid_input(field_name, value, f"Troppo lungo: {len(value)} > {max_length}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Campo {field_name} troppo lungo. Massimo: {max_length} caratteri"
            )
        
        # Verifica regex
        if regex:
            pattern = regex
        elif field_name in TEXT_FIELD_REGEX:
            pattern = TEXT_FIELD_REGEX[field_name]
        else:
            pattern = TEXT_FIELD_REGEX["description"]  # Default
        
        if not re.match(pattern, value):
            TextValidator._log_invalid_input(field_name, value, "Caratteri non validi")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Campo {field_name} contiene caratteri non validi"
            )
        
        # Verifica caratteri sospetti (SQL injection, emoji, etc.)
        suspicious_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|/\*|\*/|xp_|sp_)",
            r"[^\x00-\x7F]",  # Caratteri non ASCII (inclusi emoji)
            r"<script|javascript:|vbscript:|onload=|onerror="
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                TextValidator._log_invalid_input(field_name, value, f"Contenuto sospetto rilevato: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Campo {field_name} contiene contenuto non consentito"
                )
        
        # Log input valido
        TextValidator._log_valid_input(field_name, value)
        
        return value
    
    @staticmethod
    def _log_invalid_input(field_name: str, value: str, reason: str):
        """Logga un input non valido."""
        multi_tenant_logger.log_security_event(
            "invalid_text_input",
            {
                "field_name": field_name,
                "value_preview": value[:100] + "..." if len(value) > 100 else value,
                "reason": reason
            }
        )
        
        logger.warning(
            f"Invalid text input rejected: {field_name}",
            extra={
                "field_name": field_name,
                "value_preview": value[:100] + "..." if len(value) > 100 else value,
                "reason": reason,
                "event_type": "invalid_text_input"
            }
        )
    
    @staticmethod
    def _log_valid_input(field_name: str, value: str):
        """Logga un input valido."""
        multi_tenant_logger.info(
            f"Text input validated: {field_name}",
            {
                "field_name": field_name,
                "value_preview": value[:100] + "..." if len(value) > 100 else value,
                "event_type": "valid_text_input"
            }
        )

# Funzioni di utilità per uso diretto
def sanitize_filename(filename: str) -> str:
    """Wrapper per FileValidator.sanitize_filename."""
    return FileValidator.sanitize_filename(filename)

def is_allowed_mime_type(mime: str, filename: str) -> bool:
    """Wrapper per FileValidator.is_allowed_mime_type."""
    return FileValidator.is_allowed_mime_type(mime, filename)

def validate_file_upload(file: UploadFile, allowed_types: List[str], max_size: int) -> None:
    """Wrapper per FileValidator.validate_file_upload."""
    return FileValidator.validate_file_upload(file, allowed_types, max_size)

def validate_text_field(value: str, max_length: int, regex: str) -> None:
    """Wrapper per TextValidator.validate_text_field."""
    return TextValidator.validate_text_field(value, "field", max_length, regex)

# Decoratori per validazione automatica
def validate_file_upload_decorator(allowed_categories: Optional[List[str]] = None, max_size: Optional[int] = None):
    """Decoratore per validazione automatica file upload."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Cerca il parametro file nei kwargs
            file_param = None
            for key, value in kwargs.items():
                if isinstance(value, UploadFile):
                    file_param = value
                    break
            
            if file_param:
                safe_filename, category = FileValidator.validate_file_upload(
                    file_param, allowed_categories, max_size
                )
                # Sostituisci il filename con quello sanificato
                file_param.filename = safe_filename
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_text_fields_decorator(fields: List[str], max_length: int = 1000):
    """Decoratore per validazione automatica campi testo."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for field_name in fields:
                if field_name in kwargs and kwargs[field_name]:
                    kwargs[field_name] = TextValidator.validate_text_field(
                        kwargs[field_name], field_name, max_length
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator 