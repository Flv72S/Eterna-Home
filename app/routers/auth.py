from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.core.limiter import limiter
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService
from app.utils.security import get_current_user

router = APIRouter()
logger = get_logger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> Any:
    """
    Register a new user.
    """
    logger.info("User registration attempt", 
                email=user_data.email,
                username=user_data.username)
    
    user_service = UserService(session)
    
    # Check if user already exists by email
    existing_user = user_service.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning("User registration failed - email already exists",
                       email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = user_service.get_user_by_username(user_data.username)
    if existing_username:
        logger.warning("User registration failed - username already taken",
                       username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = user_service.create_user(user_data)
    logger.info("User registered successfully",
                user_id=user.id,
                email=user.email,
                username=user.username)
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
    logger.info("Login attempt",
                username=form_data.username,
                client_ip=request.client.host if request.client else None)
    
    user_service = UserService(session)
    result = user_service.authenticate_user(
        email_or_username=form_data.username, password=form_data.password
    )
    
    if result["error"] == "not_found" or result["error"] == "wrong_password":
        logger.warning("Login failed - invalid credentials",
                       username=form_data.username,
                       error=result["error"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if result["error"] == "disabled":
        logger.warning("Login failed - user disabled",
                       username=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato",
        )
    
    user = result["user"]
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info("Login successful",
                user_id=user.id,
                email=user.email,
                username=user.username)
    
    # Restituisci anche le informazioni dell'utente con role_display
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role": user.role,
            "role_display": user.get_display_role(),
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Refresh the access token.
    """
    logger.info("Token refresh attempt",
                user_id=current_user.id,
                email=current_user.email)
    
    if not current_user.is_active:
        logger.warning("Token refresh failed - user disabled",
                       user_id=current_user.id,
                       email=current_user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    logger.info("Token refreshed successfully",
                user_id=current_user.id,
                email=current_user.email)
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    Idempotente: restituisce sempre 200 anche con token non valido.
    TODO: In futuro implementare blacklist token per invalidazione effettiva.
    """
    logger.info("Logout request")
    return {"message": "Logout effettuato con successo"} 