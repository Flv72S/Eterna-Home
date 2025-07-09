"""
Servizio per l'autenticazione a due fattori (MFA) con TOTP.
Gestisce setup, verifica e gestione dei segreti MFA per gli utenti.
"""
import base64
import io
import pyotp
import qrcode
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from PIL import Image

from app.core.logging_config import log_security_event, get_logger
from app.models.user import User

logger = get_logger(__name__)

class MFAService:
    """Servizio per la gestione dell'autenticazione a due fattori."""
    
    def __init__(self):
        self.issuer_name = "Eterna-Home"
        self.digits = 6
        self.interval = 30  # secondi
    
    def generate_mfa_secret(self, user: User) -> str:
        """
        Genera un nuovo segreto MFA per un utente.
        
        Args:
            user: Utente per cui generare il segreto
            
        Returns:
            str: Segreto TOTP generato
        """
        try:
            # Genera un segreto casuale
            secret = pyotp.random_base32()
            
            logger.info(f"Segreto MFA generato per utente {user.id}")
            
            return secret
            
        except Exception as e:
            logger.error(f"Errore durante generazione segreto MFA: {e}")
            raise
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """
        Genera un QR code per l'app MFA.
        
        Args:
            user: Utente per cui generare il QR code
            secret: Segreto TOTP
            
        Returns:
            str: QR code in formato base64 PNG
        """
        try:
            # Crea l'URI TOTP
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name=self.issuer_name
            )
            
            # Genera il QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Crea l'immagine
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converti in base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"QR code MFA generato per utente {user.id}")
            
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            logger.error(f"Errore durante generazione QR code MFA: {e}")
            raise
    
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """
        Verifica un codice TOTP.
        
        Args:
            secret: Segreto TOTP dell'utente
            code: Codice da verificare
            
        Returns:
            bool: True se il codice è valido
        """
        try:
            totp = pyotp.TOTP(secret)
            
            # Verifica il codice con una finestra di tolleranza
            is_valid = totp.verify(code, valid_window=1)
            
            if is_valid:
                logger.info("Codice TOTP verificato con successo")
            else:
                logger.warning("Codice TOTP non valido")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Errore durante verifica codice TOTP: {e}")
            return False
    
    def setup_mfa(self, user: User) -> Dict[str, Any]:
        """
        Configura l'MFA per un utente.
        
        Args:
            user: Utente per cui configurare l'MFA
            
        Returns:
            Dict con segreto e QR code
        """
        try:
            # Genera nuovo segreto
            secret = self.generate_mfa_secret(user)
            
            # Genera QR code
            qr_code = self.generate_qr_code(user, secret)
            
            # Log dell'operazione
            log_security_event(
                event="mfa_setup",
                status="success",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "action": "setup_initiated",
                    "user_email": user.email
                }
            )
            
            return {
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": self._generate_backup_codes()
            }
            
        except Exception as e:
            logger.error(f"Errore durante setup MFA: {e}")
            log_security_event(
                event="mfa_setup",
                status="failed",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "error": str(e),
                    "user_email": user.email
                }
            )
            raise
    
    def enable_mfa(self, user: User, secret: str, verification_code: str) -> bool:
        """
        Abilita l'MFA per un utente dopo verifica del codice.
        
        Args:
            user: Utente per cui abilitare l'MFA
            secret: Segreto TOTP
            verification_code: Codice di verifica
            
        Returns:
            bool: True se l'MFA è stato abilitato
        """
        try:
            # Verifica il codice
            if not self.verify_totp_code(secret, verification_code):
                log_security_event(
                    event="mfa_enable",
                    status="failed",
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    reason="invalid_verification_code",
                    metadata={
                        "user_email": user.email
                    }
                )
                return False
            
            # Abilita l'MFA
            user.mfa_enabled = True
            user.mfa_secret = secret
            
            log_security_event(
                event="mfa_enable",
                status="success",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "user_email": user.email
                }
            )
            
            logger.info(f"MFA abilitato per utente {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante abilitazione MFA: {e}")
            log_security_event(
                event="mfa_enable",
                status="failed",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "error": str(e),
                    "user_email": user.email
                }
            )
            return False
    
    def disable_mfa(self, user: User, verification_code: str) -> bool:
        """
        Disabilita l'MFA per un utente.
        
        Args:
            user: Utente per cui disabilitare l'MFA
            verification_code: Codice di verifica
            
        Returns:
            bool: True se l'MFA è stato disabilitato
        """
        try:
            if not user.mfa_enabled or not user.mfa_secret:
                logger.warning(f"Tentativo di disabilitare MFA non abilitato per utente {user.id}")
                return False
            
            # Verifica il codice
            if not self.verify_totp_code(user.mfa_secret, verification_code):
                log_security_event(
                    event="mfa_disable",
                    status="failed",
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    reason="invalid_verification_code",
                    metadata={
                        "user_email": user.email
                    }
                )
                return False
            
            # Disabilita l'MFA
            user.mfa_enabled = False
            user.mfa_secret = None
            
            log_security_event(
                event="mfa_disable",
                status="success",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "user_email": user.email
                }
            )
            
            logger.info(f"MFA disabilitato per utente {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante disabilitazione MFA: {e}")
            log_security_event(
                event="mfa_disable",
                status="failed",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "error": str(e),
                    "user_email": user.email
                }
            )
            return False
    
    def verify_login_mfa(self, user: User, mfa_code: str) -> bool:
        """
        Verifica il codice MFA durante il login.
        
        Args:
            user: Utente che sta effettuando il login
            mfa_code: Codice MFA fornito
            
        Returns:
            bool: True se il codice è valido
        """
        try:
            if not user.mfa_enabled or not user.mfa_secret:
                logger.warning(f"Tentativo di verifica MFA per utente {user.id} senza MFA abilitato")
                return False
            
            is_valid = self.verify_totp_code(user.mfa_secret, mfa_code)
            
            if is_valid:
                log_security_event(
                    event="mfa_login",
                    status="success",
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    metadata={
                        "user_email": user.email
                    }
                )
            else:
                log_security_event(
                    event="mfa_login",
                    status="failed",
                    user_id=user.id,
                    tenant_id=user.tenant_id,
                    reason="invalid_mfa_code",
                    metadata={
                        "user_email": user.email
                    }
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Errore durante verifica MFA login: {e}")
            log_security_event(
                event="mfa_login",
                status="failed",
                user_id=user.id,
                tenant_id=user.tenant_id,
                metadata={
                    "error": str(e),
                    "user_email": user.email
                }
            )
            return False
    
    def _generate_backup_codes(self) -> list:
        """Genera codici di backup per l'MFA."""
        import secrets
        backup_codes = []
        for _ in range(10):
            code = secrets.token_hex(4).upper()[:8]
            backup_codes.append(code)
        return backup_codes

# Istanza globale del servizio
mfa_service = MFAService()

# Funzioni di utilità per compatibilità
def get_mfa_service() -> MFAService:
    """Ottiene l'istanza del servizio MFA."""
    return mfa_service 