from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional, List, Union

from app.core.config import settings
from app.db.session import get_session
from app.db.utils import safe_exec
from app.models.user import User
from app.utils.security import get_cached_user, cache_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_db():
    """Get database session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        print(f"[DEBUG] Token payload: {payload}")
        print(f"[DEBUG] Email from token: {email}")
        if email is None:
            print("[DEBUG] Email is None, raising credentials_exception")
            raise credentials_exception
    except JWTError as e:
        print(f"[DEBUG] JWT decode error: {e}")
        raise credentials_exception

    # Try to get user from cache first
    cached_user = get_cached_user(email)
    if cached_user:
        print(f"[DEBUG] User found in cache: {cached_user}")
        return User(**cached_user)

    # If not in cache, get from database
    query = select(User).where(User.email == email)
    result = safe_exec(session, query)
    user = result.first()
    print(f"[DEBUG] User from database: {user}")
    if user is None:
        print(f"[DEBUG] User not found in database for email: {email}")
        raise credentials_exception

    # Cache the user for future requests
    cache_user(user, email)
    
    return user

def require_roles(*required_roles: str):
    """
    Dependency factory per verificare che l'utente abbia uno dei ruoli richiesti.
    
    Args:
        *required_roles: Ruoli richiesti (uno o più)
    
    Returns:
        Dependency function che verifica i ruoli dell'utente
    
    Example:
        @app.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_roles("admin", "super_admin"))):
            return {"message": "Admin access granted"}
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        # Verifica se l'utente ha uno dei ruoli richiesti
        if not user.has_any_role(required_roles):
            # Log del tentativo di accesso non autorizzato
            print(f"[SECURITY] Access denied for user {user.email} (roles: {user.get_role_names()}) "
                  f"to endpoint requiring roles: {required_roles}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}. "
                       f"User roles: {', '.join(user.get_role_names())}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log dell'accesso autorizzato
        print(f"[SECURITY] Access granted for user {user.email} (roles: {user.get_role_names()}) "
              f"to endpoint requiring roles: {required_roles}")
        
        return user
    
    return role_checker

def require_single_role(required_role: str):
    """
    Dependency factory per verificare che l'utente abbia un ruolo specifico.
    
    Args:
        required_role: Ruolo richiesto
    
    Returns:
        Dependency function che verifica il ruolo dell'utente
    
    Example:
        @app.get("/super-admin-only")
        def super_admin_endpoint(user: User = Depends(require_single_role("super_admin"))):
            return {"message": "Super admin access granted"}
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if not user.has_role(required_role):
            print(f"[SECURITY] Access denied for user {user.email} (roles: {user.get_role_names()}) "
                  f"to endpoint requiring role: {required_role}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}. "
                       f"User roles: {', '.join(user.get_role_names())}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"[SECURITY] Access granted for user {user.email} (roles: {user.get_role_names()}) "
              f"to endpoint requiring role: {required_role}")
        
        return user
    
    return role_checker

# Alias per compatibilità
require_role = require_single_role 