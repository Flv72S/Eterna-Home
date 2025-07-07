from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
from app.core.config import settings
from passlib.context import CryptContext
import uuid
import json

def serialize_data_for_jwt(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serializza i dati per il token JWT, convertendo UUID in stringhe.
    
    Args:
        data: Dati da serializzare
    
    Returns:
        Dict[str, Any]: Dati serializzati
    """
    serialized = {}
    for key, value in data.items():
        if isinstance(value, uuid.UUID):
            serialized[key] = str(value)
        elif isinstance(value, list):
            # Gestisce liste che potrebbero contenere UUID
            serialized[key] = [
                str(item) if isinstance(item, uuid.UUID) else item 
                for item in value
            ]
        else:
            serialized[key] = value
    return serialized

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT di accesso.
    
    Args:
        data: Dati da includere nel token
        expires_delta: Durata di validità del token (default: 30 minuti)
    
    Returns:
        str: Token JWT codificato
    """
    # Serializza i dati per gestire UUID e altri tipi non JSON-serializable
    to_encode = serialize_data_for_jwt(data.copy())
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Crea un token JWT di refresh.
    
    Args:
        data: Dati da includere nel token
    
    Returns:
        str: Token JWT di refresh codificato
    """
    # Serializza i dati per gestire UUID e altri tipi non JSON-serializable
    to_encode = serialize_data_for_jwt(data.copy())
    
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verifica un token JWT.
    
    Args:
        token: Token JWT da verificare
        token_type: Tipo di token ("access" o "refresh")
    
    Returns:
        Dict[str, Any]: Dati del token se valido, None altrimenti
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verifica che il tipo di token sia corretto
        if payload.get("type") != token_type:
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica un token di accesso.
    
    Args:
        token: Token di accesso da verificare
    
    Returns:
        Dict[str, Any]: Dati del token se valido, None altrimenti
    """
    return verify_token(token, "access")

def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica un token di refresh.
    
    Args:
        token: Token di refresh da verificare
    
    Returns:
        Dict[str, Any]: Dati del token se valido, None altrimenti
    """
    return verify_token(token, "refresh")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una password contro il suo hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera l'hash di una password."""
    return pwd_context.hash(password) 