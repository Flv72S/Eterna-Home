from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token
from app.security.limiter import rate_limit_auth
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.user import User
from app.schemas.token import Token, TokenRefresh, TokenRevoke
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService
from app.services.mfa_service import get_mfa_service
from app.utils.security import get_current_user
import pyotp

router = APIRouter()
logger = get_logger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit_auth()
async def register_user(
    request: Request,
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> Any:
    """
    Register a new user.
    """
    logger.info("User registration attempt", 
                email=user_data.email,
                username=user_data.username,
                client_ip=request.client.host if request.client else None)
    
    # Check if user already exists by email
    existing_user = UserService.get_user_by_email(session, user_data.email)
    if existing_user:
        logger.warning("User registration failed - email already exists",
                       email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = UserService.get_user_by_username(session, user_data.username)
    if existing_username:
        logger.warning("User registration failed - username already taken",
                       username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = UserService.create_user(session, user_data)
    logger.info("User registered successfully",
                user_id=user.id,
                email=user.email,
                username=user.username)
    return user

@router.post("/token", response_model=Token)
@rate_limit_auth()
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
) -> Any:
    """
    OAuth2 compatible token login, get an access token and refresh token for future requests.
    """
    logger.info("Login attempt",
                username=form_data.username,
                client_ip=request.client.host if request.client else None)
    
    result = UserService.authenticate_user(session, email_or_username=form_data.username, password=form_data.password)
    
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
    
    # Crea access token e refresh token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": str(user.tenant_id) if user.tenant_id else None}, 
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": str(user.tenant_id) if user.tenant_id else None}
    )
    
    logger.info("Login successful",
                user_id=user.id,
                email=user.email,
                username=user.username)
    
    # Restituisci access token, refresh token e informazioni utente
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in secondi
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
@rate_limit_auth()
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    session: Session = Depends(get_session)
) -> Any:
    """
    Refresh the access token using a valid refresh token.
    """
    logger.info("Token refresh attempt",
                client_ip=request.client.host if request.client else None)
    
    # Verifica il refresh token
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        logger.warning("Token refresh failed - invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ottieni l'utente dal database
    user = UserService.get_user_by_email(session, payload.get("sub"))
    
    if not user:
        logger.warning("Token refresh failed - user not found",
                       email=payload.get("sub"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning("Token refresh failed - user disabled",
                       user_id=user.id,
                       email=user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato"
        )
    
    # Crea nuovo access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": str(user.tenant_id) if user.tenant_id else None}, 
        expires_delta=access_token_expires
    )
    
    # Crea nuovo refresh token (rotazione)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": str(user.tenant_id) if user.tenant_id else None}
    )
    
    logger.info("Token refreshed successfully",
                user_id=user.id,
                email=user.email)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in secondi
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

@router.post("/revoke")
async def revoke_token(
    request: Request,
    token_data: TokenRevoke,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Revoke a token (logout).
    TODO: Implementare blacklist token per invalidazione effettiva.
    """
    logger.info("Token revocation request",
                user_id=current_user.id,
                email=current_user.email,
                client_ip=request.client.host if request.client else None,
                reason=token_data.reason)
    
    # TODO: Aggiungere il token alla blacklist
    # blacklist_token(token_data.token, current_user.id, token_data.reason)
    
    return {"message": "Token revocato con successo"}

@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).
    """
    return {"message": "Logout successful"}

# Endpoint MFA
@router.post("/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Setup iniziale dell'MFA per un utente.
    Genera segreto e QR code per l'app MFA.
    """
    logger.info("MFA setup request",
                user_id=current_user.id,
                email=current_user.email)
    
    # Verifica che l'utente non abbia già l'MFA abilitato
    if current_user.mfa_enabled:
        logger.warning("MFA setup failed - already enabled",
                       user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MFA già abilitato per questo utente"
        )
    
    try:
        mfa_service = get_mfa_service()
        setup_data = mfa_service.setup_mfa(current_user)
        
        # Salva il segreto nel database tramite query diretta per garantire visibilità tra sessioni
        from app.models.user import User
        session.query(User).filter(User.id == current_user.id).update({
            "mfa_secret": setup_data["secret"]
        })
        session.commit()
        
        logger.info("MFA setup completed",
                    user_id=current_user.id)
        
        return {
            "message": "MFA setup completato",
            "secret": setup_data["secret"],
            "qr_code": setup_data["qr_code"],
            "backup_codes": setup_data["backup_codes"]
        }
        
    except Exception as e:
        logger.error(f"MFA setup failed: {e}",
                     user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il setup dell'MFA"
        )

@router.post("/mfa/enable")
async def enable_mfa(
    verification_code: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Abilita l'MFA per un utente dopo verifica del codice.
    """
    logger.info("MFA enable request",
                user_id=current_user.id,
                email=current_user.email)

    # Forza un refresh esplicito della sessione SQLAlchemy
    session.expire_all()
    session.commit()
    
    # Ricarica l'utente direttamente dal database per assicurarsi di avere i dati più recenti
    user = session.exec(select(User).where(User.id == current_user.id)).first()
    if not user:
        logger.error("MFA enable failed - user not found",
                     user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )

    if user.mfa_enabled:
        logger.warning("MFA enable failed - already enabled",
                       user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MFA è già abilitato"
        )

    if not user.mfa_secret:
        logger.warning("MFA enable failed - no secret found",
                       user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Esegui prima il setup dell'MFA"
        )

    # Verify the TOTP code
    try:
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(verification_code):
            logger.warning("MFA enable failed - invalid code",
                           user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Codice di verifica non valido"
            )
    except Exception as e:
        logger.error("MFA enable failed - TOTP error",
                    user_id=user.id,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Errore nella verifica del codice"
        )

    # Enable MFA tramite query diretta per garantire visibilità tra sessioni
    session.query(User).filter(User.id == user.id).update({
        "mfa_enabled": True
    })
    session.commit()

    logger.info("MFA enabled successfully",
                user_id=user.id)

    return {"message": "MFA abilitato con successo"}

@router.post("/mfa/disable")
async def disable_mfa(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Disabilita l'MFA per un utente.
    """
    logger.info("MFA disable request",
                user_id=current_user.id,
                email=current_user.email)
    
    # Ricarica l'utente dal database per vedere le modifiche più recenti
    user = session.exec(select(User).where(User.id == current_user.id)).first()
    if not user:
        logger.error("MFA disable failed - user not found",
                     user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    if not user.mfa_enabled:
        logger.warning("MFA disable failed - not enabled",
                       user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MFA non abilitato"
        )
    
    try:
        # Disabilita l'MFA tramite query diretta per garantire visibilità tra sessioni
        session.query(User).filter(User.id == user.id).update({
            "mfa_enabled": False,
            "mfa_secret": None
        })
        session.commit()
        
        logger.info("MFA disabled successfully",
                    user_id=user.id)
        return {"message": "MFA disabilitato con successo", "mfa_enabled": False}
            
    except Exception as e:
        logger.error(f"MFA disable failed: {e}",
                     user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la disabilitazione dell'MFA"
        )

@router.post("/mfa/verify")
async def verify_mfa(
    mfa_code: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Any:
    """
    Verifica un codice MFA (usato durante il login).
    """
    logger.info("MFA verification request",
                user_id=current_user.id,
                email=current_user.email)
    
    # Ricarica l'utente dal database per vedere le modifiche più recenti
    user = session.exec(select(User).where(User.id == current_user.id)).first()
    if not user:
        logger.error("MFA verification failed - user not found",
                     user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    if not user.mfa_enabled:
        logger.warning("MFA verification failed - not enabled",
                       user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MFA non abilitato"
        )
    
    try:
        mfa_service = get_mfa_service()
        is_valid = mfa_service.verify_login_mfa(user, mfa_code)
        
        if is_valid:
            logger.info("MFA verification successful",
                        user_id=user.id)
            return {"message": "Codice MFA valido", "valid": True}
        else:
            logger.warning("MFA verification failed - invalid code",
                           user_id=user.id)
            return {"message": "Codice MFA non valido", "valid": False}
            
    except Exception as e:
        logger.error(f"MFA verification failed: {e}",
                     user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la verifica dell'MFA"
        ) 