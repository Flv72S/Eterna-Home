from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.user import User
from app.services.user import UserService
from app.utils.security import create_access_token, get_current_user

router = APIRouter()

@router.post("/token")
async def login_for_access_token(
    username: str,
    password: str,
    session: Session = Depends(get_session)
):
    """Login per ottenere il token JWT."""
    user = UserService.authenticate_user(session, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout dell'utente."""
    return {"message": "Logout effettuato con successo"} 