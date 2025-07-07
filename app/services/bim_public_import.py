"""
Servizio per l'import di modelli BIM da repository pubbliche (PA).
Gestisce download, validazione MIME, sicurezza e logging per fonti esterne.
"""

import logging
import uuid
import os
import mimetypes
import aiohttp
import tempfile
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from urllib.parse import urlparse
import re

# Configurazione del logger
logger = logging.getLogger(__name__)

class BIMPublicImportService:
    """
    Servizio per l'import di modelli BIM da repository pubbliche.
    """
    
    # Formati BIM supportati
    SUPPORTED_EXTENSIONS = ['.ifc', '.dxf', '.pdf']
    SUPPORTED_MIME_TYPES = [
        'application/octet-stream',
        'model/ifc',
        'application/ifc',
        'application/dxf',
        'application/pdf',
        'text/plain'  # Per alcuni file IFC
    ]
    
    # Dimensioni massime file (500MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024
    
    # Timeout per download (30 secondi)
    DOWNLOAD_TIMEOUT = 30
    
    # Domini autorizzati per repository pubblici
    AUTHORIZED_DOMAINS = [
        'geoportale.regione.',
        'www.catasto.it',
        '.comune.',
        '.gov.it',
        '.it'  # Domini italiani generici
    ]
    
    def __init__(self):
        """Inizializza il servizio di import pubblico."""
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Ottiene o crea una sessione HTTP."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.DOWNLOAD_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _validate_url(self, url: str) -> bool:
        """
        Valida l'URL per sicurezza.
        
        Args:
            url: URL da validare
        
        Returns:
            bool: True se l'URL è valido e sicuro
        
        Raises:
            HTTPException: Se l'URL non è valido
        """
        try:
            parsed = urlparse(url)
            
            # Verifica protocollo
            if parsed.scheme not in ['http', 'https']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo protocolli HTTP e HTTPS sono supportati"
                )
            
            # Verifica dominio autorizzato
            domain = parsed.netloc.lower()
            is_authorized = any(authorized in domain for authorized in self.AUTHORIZED_DOMAINS)
            
            if not is_authorized:
                logger.warning(f"Tentativo di accesso a dominio non autorizzato: {domain}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dominio non autorizzato per l'importazione"
                )
            
            # Verifica che l'URL non contenga caratteri sospetti
            suspicious_patterns = [
                r'\.\./',  # Directory traversal
                r'javascript:',  # XSS
                r'data:',  # Data URLs
                r'file:',  # File protocol
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    logger.warning(f"URL contiene pattern sospetto: {pattern}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="URL contiene caratteri non sicuri"
                    )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore validazione URL {url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL non valido"
            )
    
    def _validate_file_extension(self, filename: str) -> bool:
        """
        Valida l'estensione del file.
        
        Args:
            filename: Nome del file
        
        Returns:
            bool: True se l'estensione è supportata
        """
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in self.SUPPORTED_EXTENSIONS
    
    def _validate_mime_type(self, content_type: str) -> bool:
        """
        Valida il tipo MIME del file.
        
        Args:
            content_type: Content-Type del file
        
        Returns:
            bool: True se il tipo MIME è supportato
        """
        if not content_type:
            return False
        
        # Estrai il tipo MIME principale
        mime_type = content_type.split(';')[0].strip().lower()
        return mime_type in self.SUPPORTED_MIME_TYPES
    
    def _validate_file_size(self, content_length: int) -> bool:
        """
        Valida la dimensione del file.
        
        Args:
            content_length: Dimensione del file in bytes
        
        Returns:
            bool: True se la dimensione è accettabile
        """
        return content_length <= self.MAX_FILE_SIZE
    
    async def download_and_validate_file(
        self,
        url: str,
        tenant_id: uuid.UUID,
        house_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scarica e valida un file BIM da un URL pubblico.
        
        Args:
            url: URL del file da scaricare
            tenant_id: ID del tenant per logging
            house_id: ID della casa per logging (opzionale)
        
        Returns:
            Dict con metadati del file scaricato
        
        Raises:
            HTTPException: Se il download o la validazione falliscono
        """
        try:
            # Validazione URL
            self._validate_url(url)
            
            # Ottieni sessione HTTP
            session = await self._get_session()
            
            logger.info(f"Inizio download file BIM pubblico: {url} (tenant: {tenant_id}, house: {house_id})")
            
            # Download del file
            async with session.get(url) as response:
                # Verifica status code
                if response.status != 200:
                    logger.error(f"Download fallito con status {response.status}: {url}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Download fallito: status {response.status}"
                    )
                
                # Verifica dimensione file
                content_length = response.headers.get('content-length')
                if content_length:
                    file_size = int(content_length)
                    if not self._validate_file_size(file_size):
                        logger.error(f"File troppo grande: {file_size} bytes")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File troppo grande: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
                        )
                
                # Leggi contenuto
                content = await response.read()
                
                # Verifica dimensione effettiva
                if not self._validate_file_size(len(content)):
                    logger.error(f"File troppo grande (effettivo): {len(content)} bytes")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File troppo grande: {len(content)} bytes (max: {self.MAX_FILE_SIZE})"
                    )
                
                # Ottieni metadati
                content_type = response.headers.get('content-type', 'application/octet-stream')
                filename = self._extract_filename(response, url)
                
                # Validazione tipo MIME
                if not self._validate_mime_type(content_type):
                    logger.warning(f"Tipo MIME non supportato: {content_type}")
                    # Non blocchiamo per compatibilità, ma logghiamo
                
                # Validazione estensione
                if not self._validate_file_extension(filename):
                    logger.error(f"Estensione file non supportata: {filename}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tipo di file non supportato: {filename}"
                    )
                
                logger.info(
                    f"File BIM pubblico scaricato con successo: {filename} "
                    f"(size: {len(content)}, type: {content_type})"
                )
                
                return {
                    "content": content,
                    "filename": filename,
                    "content_type": content_type,
                    "file_size": len(content),
                    "url": url,
                    "tenant_id": str(tenant_id),
                    "house_id": house_id
                }
                
        except HTTPException:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Errore di rete durante download {url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Errore di rete durante il download"
            )
        except Exception as e:
            logger.error(f"Errore generico durante download {url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il download del file"
            )
    
    def _extract_filename(self, response: aiohttp.ClientResponse, url: str) -> str:
        """
        Estrae il nome del file dalla risposta HTTP o dall'URL.
        
        Args:
            response: Risposta HTTP
            url: URL originale
        
        Returns:
            str: Nome del file
        """
        # Prova a estrarre da Content-Disposition
        content_disposition = response.headers.get('content-disposition', '')
        if content_disposition:
            import re
            filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
            if filename_match:
                filename = filename_match.group(1).strip('"\'')
                if filename:
                    return filename
        
        # Estrai dall'URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path:
            filename = os.path.basename(path)
            if filename:
                return filename
        
        # Fallback: genera nome basato su timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"bim_public_{timestamp}.ifc"
    
    async def close(self):
        """Chiude la sessione HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Distruttore per chiudere la sessione."""
        if self.session and not self.session.closed:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
            except:
                pass 