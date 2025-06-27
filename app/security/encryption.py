"""
Modulo per la crittografia AES-256 dei file sensibili.
Implementa cifratura/decifratura con gestione chiavi per tenant.
"""
import os
import base64
import uuid
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import secrets

from app.core.logging_config import log_security_event, get_logger

logger = get_logger(__name__)

# Mock storage per le chiavi (in produzione usare KMS/HSM)
_tenant_keys: Dict[str, bytes] = {}

class EncryptionService:
    """Servizio per la crittografia dei file sensibili."""
    
    def __init__(self):
        self.algorithm = algorithms.AES
        self.key_size = 256
        self.mode = modes.GCM
        self.backend = default_backend()
    
    def generate_tenant_key(self, tenant_id: str) -> bytes:
        """Genera una chiave AES-256 per un tenant specifico."""
        key = os.urandom(32)  # 256 bit
        _tenant_keys[tenant_id] = key
        logger.info(f"Chiave generata per tenant {tenant_id}")
        return key
    
    def get_tenant_key(self, tenant_id: str) -> bytes:
        """Ottiene la chiave per un tenant, generandola se non esiste."""
        if tenant_id not in _tenant_keys:
            return self.generate_tenant_key(tenant_id)
        return _tenant_keys[tenant_id]
    
    def encrypt_file(self, content: bytes, tenant_id: str) -> Tuple[bytes, str]:
        """
        Cifra un file usando AES-256-GCM.
        
        Args:
            content: Contenuto del file da cifrare
            tenant_id: ID del tenant per la chiave
            
        Returns:
            Tuple[bytes, str]: (contenuto cifrato, nonce in base64)
        """
        try:
            key = self.get_tenant_key(tenant_id)
            nonce = os.urandom(12)  # 96 bit per GCM
            
            # Crea cipher AES-256-GCM
            cipher = Cipher(
                self.algorithm(key),
                self.mode(nonce),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            # Cifra il contenuto
            ciphertext = encryptor.update(content) + encryptor.finalize()
            
            # Combina nonce + tag + ciphertext
            tag = encryptor.tag
            encrypted_data = nonce + tag + ciphertext
            
            # Log dell'operazione
            log_security_event(
                event="file_encryption",
                status="success",
                metadata={
                    "tenant_id": tenant_id,
                    "content_size": len(content),
                    "encrypted_size": len(encrypted_data),
                    "algorithm": "AES-256-GCM"
                }
            )
            
            return encrypted_data, base64.b64encode(nonce).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Errore durante cifratura file: {e}")
            log_security_event(
                event="file_encryption",
                status="failed",
                metadata={
                    "tenant_id": tenant_id,
                    "error": str(e)
                }
            )
            raise
    
    def decrypt_file(self, encrypted_content: bytes, tenant_id: str) -> bytes:
        """
        Decifra un file usando AES-256-GCM.
        
        Args:
            encrypted_content: Contenuto cifrato
            tenant_id: ID del tenant per la chiave
            
        Returns:
            bytes: Contenuto decifrato
        """
        try:
            key = self.get_tenant_key(tenant_id)
            
            # Estrai nonce, tag e ciphertext
            nonce = encrypted_content[:12]
            tag = encrypted_content[12:28]
            ciphertext = encrypted_content[28:]
            
            # Crea cipher per decifratura
            cipher = Cipher(
                self.algorithm(key),
                self.mode(nonce, tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decifra il contenuto
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Log dell'operazione
            log_security_event(
                event="file_decryption",
                status="success",
                metadata={
                    "tenant_id": tenant_id,
                    "encrypted_size": len(encrypted_content),
                    "decrypted_size": len(plaintext)
                }
            )
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Errore durante decifratura file: {e}")
            log_security_event(
                event="file_decryption",
                status="failed",
                metadata={
                    "tenant_id": tenant_id,
                    "error": str(e)
                }
            )
            raise
    
    def generate_encrypted_path(self, tenant_id: str, original_filename: str) -> str:
        """
        Genera un path sicuro per i file cifrati.
        
        Args:
            tenant_id: ID del tenant
            original_filename: Nome originale del file
            
        Returns:
            str: Path sicuro per il file cifrato
        """
        # Genera UUID per anonimizzazione
        file_uuid = str(uuid.uuid4())
        
        # Estrai estensione originale (se presente)
        _, ext = os.path.splitext(original_filename)
        
        # Per file sensibili, usa sempre .bin per anonimizzazione
        if ext.lower() in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ifc', '.rvt']:
            ext = '.bin'
        
        return f"tenants/{tenant_id}/encrypted/{file_uuid}{ext}"
    
    def is_encrypted_file(self, file_path: str) -> bool:
        """Verifica se un file è cifrato basandosi sul path."""
        return "encrypted" in file_path
    
    def rotate_tenant_key(self, tenant_id: str) -> bool:
        """
        Ruota la chiave di un tenant (in produzione richiederebbe re-cifratura di tutti i file).
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            bool: True se la rotazione è riuscita
        """
        try:
            if tenant_id in _tenant_keys:
                del _tenant_keys[tenant_id]
            
            # Genera nuova chiave
            self.generate_tenant_key(tenant_id)
            
            log_security_event(
                event="key_rotation",
                status="success",
                metadata={
                    "tenant_id": tenant_id
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Errore durante rotazione chiave: {e}")
            log_security_event(
                event="key_rotation",
                status="failed",
                metadata={
                    "tenant_id": tenant_id,
                    "error": str(e)
                }
            )
            return False

# Istanza globale del servizio
encryption_service = EncryptionService()

# Funzioni di utilità per compatibilità
def encrypt_file(content: bytes, tenant_id: str) -> Tuple[bytes, str]:
    """Wrapper per la cifratura di file."""
    return encryption_service.encrypt_file(content, tenant_id)

def decrypt_file(encrypted_content: bytes, tenant_id: str) -> bytes:
    """Wrapper per la decifratura di file."""
    return encryption_service.decrypt_file(encrypted_content, tenant_id)

def generate_encrypted_path(tenant_id: str, original_filename: str) -> str:
    """Wrapper per la generazione di path cifrati."""
    return encryption_service.generate_encrypted_path(tenant_id, original_filename) 