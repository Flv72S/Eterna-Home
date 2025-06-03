from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from app.core.config import settings
from passlib.context import CryptContext

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT di accesso.
    
    Args:
        data: Dati da includere nel token
        expires_delta: Durata di validità del token (default: 30 minuti)
    
    Returns:
        str: Token JWT codificato
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una password contro il suo hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera l'hash di una password."""
    return pwd_context.hash(password) 