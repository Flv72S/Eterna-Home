from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_session
from app.models.user import User
from app.schemas.token import Token
from app.services.user import UserService
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = UserService.authenticate(
        session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Refresh the access token.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            data={"sub": current_user.email}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout the current user.
    """
    # In una implementazione reale, qui potremmo aggiungere il token a una blacklist
    # o invalidarlo in qualche modo. Per ora, il client dovrà semplicemente
    # rimuovere il token dalla sua memoria.
    return {"message": "Successfully logged out"} 