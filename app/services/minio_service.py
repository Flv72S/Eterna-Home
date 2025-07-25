"""
Servizio MinIO per la gestione dello storage multi-tenant.
Integra path dinamici basati su tenant_id per isolamento completo.
"""

import uuid
import json
from typing import Optional, List, BinaryIO, Dict, Any
from fastapi import UploadFile, HTTPException, status
from minio import Minio
from minio.error import S3Error
import io
import logging
from datetime import datetime, timezone
import os

from app.core.config import settings
from app.core.storage_utils import (
    get_tenant_storage_path,
    get_tenant_folder_path,
    sanitize_filename,
    validate_file_type,
    generate_unique_filename,
    parse_tenant_from_path,
    is_valid_tenant_path,
    get_allowed_extensions_for_folder,
    validate_folder
)
from app.services.antivirus_service import get_antivirus_service
from app.security.encryption import encryption_service, generate_encrypted_path

# Configurazione logging
logger = logging.getLogger(__name__)

class MinIOService:
    """
    Servizio per la gestione dello storage su MinIO con supporto multi-tenant.
    """
    
    def __init__(self, initialize_connection: bool = True):
        """
        Inizializza il client MinIO.
        
        Args:
            initialize_connection: Se True, tenta di connettersi a MinIO
        """
        self.client = None
        self.bucket_name = settings.MINIO_BUCKET_NAME
        
        # Inizializza la connessione se richiesto
        if initialize_connection:
            self._initialize_client()
            self._ensure_bucket_exists()
        else:
            logger.info("MinIO client non inizializzato")
    
    def _initialize_client(self):
        """Inizializza il client MinIO."""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL
            )
            logger.info("Client MinIO inizializzato con successo")
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del client MinIO: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella configurazione dello storage"
            )
    
    def _ensure_bucket_exists(self):
        """Assicura che il bucket esista e sia configurato come privato."""
        if not self.client:
            return
            
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} creato con successo")
            
            # Configura il bucket come privato (rimuove accesso pubblico)
            self._configure_bucket_private()
            
        except S3Error as e:
            logger.error(f"Errore nella creazione/configurazione del bucket: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella configurazione dello storage"
            )
    
    def _configure_bucket_private(self):
        """Configura il bucket come completamente privato."""
        try:
            # Rimuove tutte le policy pubbliche
            try:
                self.client.delete_bucket_policy(self.bucket_name)
                logger.info(f"Rimosse policy pubbliche dal bucket {self.bucket_name}")
            except S3Error:
                # Il bucket potrebbe non avere policy, ignoriamo l'errore
                pass
            
            # Imposta policy privata esplicita
            private_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyPublicRead",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*",
                        "Condition": {
                            "StringEquals": {
                                "aws:PrincipalType": "Anonymous"
                            }
                        }
                    }
                ]
            }
            
            self.client.set_bucket_policy(self.bucket_name, json.dumps(private_policy))
            logger.info(f"Bucket {self.bucket_name} configurato come privato")
            
        except S3Error as e:
            logger.warning(f"Non è stato possibile configurare la policy del bucket: {e}")
            # Non blocchiamo l'operazione se la policy non può essere impostata
    
    def _get_content_type(self, filename: str) -> str:
        """Determina il content type del file basato sull'estensione."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _generate_object_name(self, filename: str, folder: str = None) -> str:
        """Genera un nome oggetto unico per MinIO."""
        import hashlib
        from datetime import datetime
        
        # Genera timestamp e ID unico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:8]
        
        # Estrai nome e estensione
        name, ext = os.path.splitext(filename)
        
        # Costruisci il nome oggetto
        object_name = f"{timestamp}_{unique_id}_{name}{ext}"
        
        # Aggiungi folder se specificato
        if folder:
            object_name = f"{folder}/{object_name}"
        
        return object_name

    async def upload_file(
        self,
        file: UploadFile,
        folder: str,
        tenant_id: uuid.UUID,
        house_id: Optional[int] = None,
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Carica un file nel path del tenant specificato.
        
        Args:
            file: File da caricare
            folder: Cartella di destinazione (documents, bim, media, etc.)
            tenant_id: ID del tenant per isolamento
            house_id: ID della casa per isolamento multi-house (opzionale)
            custom_filename: Nome file personalizzato (opzionale)
        
        Returns:
            Dict con metadati del file caricato
        
        Raises:
            HTTPException: Se il file non è valido o il caricamento fallisce
        """
        try:
            # Valida la cartella
            if not validate_folder(folder):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cartella non supportata: {folder}"
                )
            
            # Valida il tipo di file
            allowed_extensions = get_allowed_extensions_for_folder(folder)
            if not validate_file_type(file.filename, allowed_extensions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo di file non consentito per la cartella {folder}. "
                           f"Estensioni consentite: {allowed_extensions}"
                )
            
            # Genera nome file unico
            if custom_filename:
                filename = sanitize_filename(custom_filename)
            else:
                filename = generate_unique_filename(file.filename, tenant_id)
            
            # Genera path multi-tenant e multi-house
            if house_id:
                storage_path = f"tenants/{tenant_id}/houses/{house_id}/{folder}/{filename}"
            else:
                storage_path = get_tenant_storage_path(folder, tenant_id, filename)
            
            # Leggi il contenuto del file
            file_content = file.file.read()
            file_size = len(file_content)
            
            # Determina se il file deve essere cifrato (file sensibili)
            sensitive_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ifc', '.rvt', '.dwg']
            should_encrypt = any(file.filename.lower().endswith(ext) for ext in sensitive_extensions)
            
            # Cifra il file se necessario
            is_encrypted = False
            if should_encrypt:
                try:
                    # Cifra il contenuto
                    encrypted_content, nonce = encryption_service.encrypt_file(file_content, str(tenant_id))
                    
                    # Genera path cifrato
                    encrypted_filename = generate_encrypted_path(str(tenant_id), file.filename)
                    
                    # Aggiorna contenuto e path per il salvataggio
                    file_content = encrypted_content
                    file_size = len(encrypted_content)
                    storage_path = encrypted_filename
                    is_encrypted = True
                    
                    logger.info(f"File cifrato: {file.filename} -> {encrypted_filename}")
                    
                except Exception as e:
                    logger.error(f"Errore durante cifratura file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Errore durante la cifratura del file"
                    )
            
            # Scansione antivirus (Micro-step 2.3)
            antivirus_service = get_antivirus_service()
            is_clean, scan_results = await antivirus_service.scan_file(file, file_content)
            
            if not is_clean:
                logger.warning(f"File rifiutato per motivi di sicurezza: {file.filename}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File rifiutato per motivi di sicurezza. Minacce rilevate: {scan_results.get('threats_found', [])}"
                )
            
            logger.info(f"File scansionato con successo: {file.filename} (scan_method: {scan_results.get('scan_method')})")
            
            # In modalità sviluppo/test, simula il caricamento
            if not self.client:
                logger.info(
                    f"[DEV] Simulazione upload file: {storage_path} "
                    f"(tenant: {tenant_id}, house: {house_id}, size: {file_size})"
                )
                return {
                    "filename": filename,
                    "original_filename": file.filename,
                    "storage_path": storage_path,
                    "file_size": file_size,
                    "content_type": file.content_type,
                    "tenant_id": str(tenant_id),
                    "house_id": house_id,
                    "folder": folder,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "is_encrypted": is_encrypted,
                    "dev_mode": True
                }
            
            # Carica su MinIO (solo in produzione)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=file.content_type
            )
            
            # Log dell'operazione
            logger.info(
                f"File caricato: {storage_path} "
                f"(tenant: {tenant_id}, house: {house_id}, size: {file_size})"
            )
            
            return {
                "filename": filename,
                "original_filename": file.filename,
                "storage_path": storage_path,
                "file_size": file_size,
                "content_type": file.content_type,
                "tenant_id": str(tenant_id),
                "house_id": house_id,
                "folder": folder,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "is_encrypted": is_encrypted
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Errore durante upload file: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "house_id": house_id,
                    "folder": folder,
                    "filename": file.filename
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il caricamento del file"
            )
    
    def download_file(
        self,
        storage_path: str,
        tenant_id: uuid.UUID,
        house_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scarica un file dal path del tenant specificato.
        
        Args:
            storage_path: Path del file nello storage
            tenant_id: ID del tenant per isolamento
            house_id: ID della casa per isolamento multi-house (opzionale)
        
        Returns:
            Dict con contenuto e metadati del file
        
        Raises:
            HTTPException: Se il file non esiste o il download fallisce
        """
        try:
            # Verifica che il path appartenga al tenant
            if not is_valid_tenant_path(storage_path, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accesso non autorizzato al file"
                )
            
            # In modalità sviluppo/test, simula il download
            if not self.client:
                logger.info(
                    f"[DEV] Simulazione download file: {storage_path} "
                    f"(tenant: {tenant_id}, house: {house_id})"
                )
                
                # Simula contenuto cifrato se il file è nel path encrypted
                is_encrypted = encryption_service.is_encrypted_file(storage_path)
                content = b"Simulated encrypted file content" if is_encrypted else b"Simulated file content for development"
                
                return {
                    "filename": os.path.basename(storage_path),
                    "content": content,
                    "content_type": "application/octet-stream",
                    "file_size": 1024,
                    "tenant_id": str(tenant_id),
                    "house_id": house_id,
                    "is_encrypted": is_encrypted,
                    "dev_mode": True
                }
            
            # Scarica da MinIO (solo in produzione)
            try:
                response = self.client.get_object(self.bucket_name, storage_path)
                file_content = response.read()
                file_size = len(file_content)
                
                # Determina content type
                content_type = response.headers.get('content-type', 'application/octet-stream')
                
                # Verifica se il file è cifrato e decifralo se necessario
                is_encrypted = encryption_service.is_encrypted_file(storage_path)
                if is_encrypted:
                    try:
                        file_content = encryption_service.decrypt_file(file_content, str(tenant_id))
                        file_size = len(file_content)
                        logger.info(f"File decifrato: {storage_path}")
                    except Exception as e:
                        logger.error(f"Errore durante decifratura file {storage_path}: {e}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Errore durante la decifratura del file"
                        )
                
                logger.info(
                    f"File scaricato: {storage_path} "
                    f"(tenant: {tenant_id}, house: {house_id}, size: {file_size}, encrypted: {is_encrypted})"
                )
                
                return {
                    "filename": os.path.basename(storage_path),
                    "content": file_content,
                    "content_type": content_type,
                    "file_size": file_size,
                    "tenant_id": str(tenant_id),
                    "house_id": house_id,
                    "is_encrypted": is_encrypted
                }
                
            except S3Error as e:
                if e.code == 'NoSuchKey':
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="File non trovato"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Errore durante il download del file"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Errore durante download file: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "house_id": house_id,
                    "storage_path": storage_path
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il download del file"
            )
    
    def delete_file(
        self,
        storage_path: str,
        tenant_id: uuid.UUID
    ) -> bool:
        """
        Elimina un file verificando l'accesso del tenant.
        
        Args:
            storage_path: Path del file su MinIO
            tenant_id: ID del tenant per verifica accesso
        
        Returns:
            bool: True se il file è stato eliminato
        
        Raises:
            HTTPException: Se l'accesso è negato
        """
        try:
            # Verifica che il path appartenga al tenant
            if not is_valid_tenant_path(storage_path, tenant_id):
                logger.warning(f"Tentativo di eliminazione non autorizzato: {storage_path} (tenant: {tenant_id})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accesso negato al file"
                )
            
            # In modalità sviluppo/test, simula l'eliminazione
            if not self.client:
                logger.info(f"[DEV] Simulazione eliminazione file: {storage_path} (tenant: {tenant_id})")
                return True
            
            # Elimina il file da MinIO (solo in produzione)
            self.client.remove_object(self.bucket_name, storage_path)
            
            # Log dell'operazione
            logger.info(f"File eliminato: {storage_path} (tenant: {tenant_id})")
            
            return True
            
        except S3Error as e:
            logger.error(f"Errore MinIO durante eliminazione: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante l'eliminazione del file"
            )
        except Exception as e:
            logger.error(f"Errore generico durante eliminazione: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def list_files(
        self,
        folder: str,
        tenant_id: uuid.UUID,
        prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista i file in una cartella del tenant.
        
        Args:
            folder: Cartella da listare
            tenant_id: ID del tenant
            prefix: Prefisso per filtrare i file (opzionale)
        
        Returns:
            Lista con metadati dei file
        """
        try:
            # Genera il path della cartella tenant
            folder_path = get_tenant_folder_path(folder, tenant_id)
            
            # Aggiungi prefisso se specificato
            if prefix:
                folder_path += prefix
            
            # In modalità sviluppo/test, simula il listaggio
            if not self.client:
                logger.info(f"[DEV] Simulazione listaggio file: {folder_path} (tenant: {tenant_id})")
                return [
                    {
                        "filename": "test_file.pdf",
                        "storage_path": f"{folder_path}test_file.pdf",
                        "file_size": 1024,
                        "content_type": "application/pdf",
                        "last_modified": datetime.now(timezone.utc),
                        "tenant_id": str(tenant_id),
                        "dev_mode": True
                    }
                ]
            
            # Lista gli oggetti (solo in produzione)
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=folder_path,
                recursive=True
            )
            
            files = []
            for obj in objects:
                # Ottieni metadati
                stat = self.client.stat_object(self.bucket_name, obj.object_name)
                
                files.append({
                    "filename": obj.object_name.split('/')[-1],
                    "storage_path": obj.object_name,
                    "file_size": stat.size,
                    "content_type": stat.content_type,
                    "last_modified": stat.last_modified,
                    "tenant_id": str(tenant_id)
                })
            
            return files
            
        except S3Error as e:
            logger.error(f"Errore MinIO durante listaggio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante il listaggio dei file"
            )
    
    def get_file_info(
        self,
        storage_path: str,
        tenant_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Ottiene informazioni su un file specifico.
        
        Args:
            storage_path: Path del file su MinIO
            tenant_id: ID del tenant per verifica accesso
        
        Returns:
            Dict con metadati del file
        """
        try:
            # Verifica che il path appartenga al tenant
            if not is_valid_tenant_path(storage_path, tenant_id):
                logger.warning(f"Tentativo di accesso non autorizzato: {storage_path} (tenant: {tenant_id})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accesso negato al file"
                )
            
            # In modalità sviluppo/test, simula le info
            if not self.client:
                logger.info(f"[DEV] Simulazione info file: {storage_path} (tenant: {tenant_id})")
                return {
                    "filename": storage_path.split('/')[-1],
                    "storage_path": storage_path,
                    "file_size": 1024,
                    "content_type": "application/octet-stream",
                    "last_modified": datetime.now(timezone.utc),
                    "tenant_id": str(tenant_id),
                    "dev_mode": True
                }
            
            # Ottieni metadati (solo in produzione)
            stat = self.client.stat_object(self.bucket_name, storage_path)
            
            return {
                "filename": storage_path.split('/')[-1],
                "storage_path": storage_path,
                "file_size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "tenant_id": str(tenant_id)
            }
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            else:
                logger.error(f"Errore MinIO durante get info: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Errore durante il recupero delle informazioni del file"
                )
    
    def create_presigned_url(
        self,
        storage_path: str,
        tenant_id: uuid.UUID,
        method: str = "GET",
        expires: int = 3600
    ) -> Optional[str]:
        """
        Crea un URL pre-firmato per accesso temporaneo al file.
        
        Args:
            storage_path: Path del file su MinIO
            tenant_id: ID del tenant per verifica accesso
            method: Metodo HTTP (GET, PUT, DELETE)
            expires: Scadenza in secondi
        
        Returns:
            URL pre-firmato
        """
        try:
            # Verifica che il path appartenga al tenant
            if not is_valid_tenant_path(storage_path, tenant_id):
                logger.warning(f"Tentativo di creazione URL non autorizzato: {storage_path} (tenant: {tenant_id})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Accesso negato al file"
                )
            
            # In modalità sviluppo/test, simula l'URL
            if not self.client:
                logger.info(f"[DEV] Simulazione URL pre-firmato: {storage_path} (tenant: {tenant_id})")
                return f"http://localhost:9000/{self.bucket_name}/{storage_path}?dev_mode=true"
            
            # Crea URL pre-firmato (solo in produzione)
            url = self.client.presigned_url(
                method=method,
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"Errore MinIO durante creazione URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la creazione dell'URL"
            )

def get_minio_service() -> MinIOService:
    """
    Dependency per ottenere un'istanza del servizio MinIO.
    Inizializza la connessione solo in produzione.
    """
    return MinIOService(initialize_connection=False)  # Non inizializza in sviluppo

# TODO: Implementare cleanup automatico dei file temporanei
# TODO: Aggiungere metriche di utilizzo storage per tenant
# TODO: Implementare backup automatico dei file critici
# TODO: Aggiungere validazione automatica dei path durante operazioni 