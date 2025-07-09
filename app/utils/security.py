from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
import logging

from app.core.config import settings
from app.db.session import get_session
from app.models.user import User
from app.services.user import UserService
from app.utils.password import get_password_hash, verify_password

# Configurazione del contesto per l'hashing delle password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Cache semplice per gli utenti (in produzione usare Redis)
_user_cache: Dict[str, Dict[str, Any]] = {}

def get_cached_user(email: str) -> Optional[Dict[str, Any]]:
    """Ottiene un utente dalla cache"""
    return _user_cache.get(email)

def cache_user(user: User, email: str) -> None:
    """Salva un utente nella cache"""
    _user_cache[email] = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT token con i dati forniti."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Converti il datetime in timestamp per il test
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica un JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Verifica il token JWT e restituisce l'utente corrente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Istanzia il service correttamente
    user = UserService.get_user_by_email(session, email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    # Assicurati che tutti i campi necessari siano presenti
    if not user.username:
        user.username = user.email.split('@')[0]
    if not user.full_name:
        user.full_name = user.username
    
    # Restituisci solo i campi necessari
    return User(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

def log_security_event(event_type: str, user_id: int = None, tenant_id: str = None, details: dict = None):
    """
    Logga un evento di sicurezza rilevante (upload manuali, errori, ecc).
    """
    logger = logging.getLogger("security")
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"SECURITY_EVENT: {log_data}") 