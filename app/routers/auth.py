from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.core.limiter import limiter
from app.db.session import get_session
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> Any:
    """
    Register a new user.
    """
    user_service = UserService(session)
    
    # Check if user already exists
    existing_user = user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = user_service.create_user(user_data)
    return user

@router.post("/token", response_model=Token)
@limiter.limit("1000/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user_service = UserService(session)
    result = user_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if result["error"] == "not_found" or result["error"] == "wrong_password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if result["error"] == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato",
        )
    user = result["user"]
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
async def logout():
    """
    Logout endpoint.
    Idempotente: restituisce sempre 200 anche con token non valido.
    TODO: In futuro implementare blacklist token per invalidazione effettiva.
    """
    return {"message": "Logout effettuato con successo"} 