from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import logging

from db.session import get_db
from models.user import User
from config.settings import settings

# Carica le variabili d'ambiente
load_dotenv()

# Configura il logger
logger = logging.getLogger(__name__)

# Configurazione
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # Usa una variabile d'ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Verifico la password")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    logger.debug("Genero l'hash della password")
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    logger.debug("Creo il token di accesso")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.debug("Token creato con successo")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Errore durante la creazione del token: {str(e)}", exc_info=True)
        raise

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def create_user(db: Session, email: str, hashed_password: str) -> User:
    logger.debug(f"Creo l'utente nel database: {email}")
    try:
        db_user = User(email=email, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Utente creato con successo nel database: {email}")
        return db_user
    except Exception as e:
        logger.error(f"Errore durante la creazione dell'utente nel database: {str(e)}", exc_info=True)
        db.rollback()
        raise

async def role_required(roles: List[str], current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user 