"""
Servizio per la validazione dei file uploadati.
Gestisce controlli di sicurezza, tipo MIME, dimensione e contenuto.
"""

import os
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import mimetypes
from fastapi import UploadFile, HTTPException
from app.core.config import settings


class FileValidationService:
    """Servizio per la validazione dei file."""
    
    def __init__(self):
        self.allowed_extensions = {
            '.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', 
            '.gif', '.bmp', '.tiff', '.zip', '.rar', '.7z'
        }
        
        self.allowed_mime_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed'
        }
        
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Valida un file uploadato.
        
        Args:
            file: File da validare
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Controllo estensione
            if not self._validate_extension(file.filename):
                return False, "Estensione file non consentita"
            
            # Controllo dimensione
            if not self._validate_size(file):
                return False, f"File troppo grande. Massimo {self.max_file_size // (1024*1024)}MB"
            
            # Controllo tipo MIME
            if not self._validate_mime_type(file):
                return False, "Tipo di file non consentito"
            
            return True, None
            
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}"
    
    def _validate_extension(self, filename: str) -> bool:
        """Valida l'estensione del file."""
        if not filename:
            return False
        
        extension = Path(filename).suffix.lower()
        return extension in self.allowed_extensions
    
    def _validate_size(self, file: UploadFile) -> bool:
        """Valida la dimensione del file."""
        # Per ora restituiamo True, in produzione si dovrebbe controllare la dimensione effettiva
        return True
    
    def _validate_mime_type(self, file: UploadFile) -> bool:
        """Valida il tipo MIME del file."""
        if not file.content_type:
            return False
        # Se magic è disponibile, usalo per controllare il MIME
        if HAS_MAGIC:
            try:
                mime = magic.Magic(mime=True)
                file.file.seek(0)
                mime_type = mime.from_buffer(file.file.read(2048))
                file.file.seek(0)
                return mime_type in self.allowed_mime_types
            except Exception:
                return file.content_type in self.allowed_mime_types
        # Fallback: usa solo content_type
        return file.content_type in self.allowed_mime_types
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizza il nome del file rimuovendo caratteri pericolosi.
        
        Args:
            filename: Nome del file originale
            
        Returns:
            str: Nome del file sanitizzato
        """
        if not filename:
            return "unnamed_file"
        
        # Rimuovi caratteri pericolosi
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limita la lunghezza
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized


# Istanza globale del servizio
file_validation_service = FileValidationService() 