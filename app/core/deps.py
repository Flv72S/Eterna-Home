from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional, List, Union
import uuid

from app.core.config import settings
from app.db.session import get_session
from app.db.utils import safe_exec
from app.models.user import User
from app.utils.security import get_cached_user, cache_user

# Note: Le funzioni RBAC multi-tenant sono disponibili in app.core.auth.rbac
# Per evitare import circolari, importarle direttamente nei router:
# from app.core.auth.rbac import require_permission_in_tenant, require_role_in_tenant, etc.

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

async def get_current_tenant(
    current_user: User = Depends(get_current_user)
) -> uuid.UUID:
    """
    Dependency per ottenere il tenant_id dell'utente corrente.
    
    Returns:
        uuid.UUID: Il tenant_id dell'utente autenticato
        
    Raises:
        HTTPException: Se l'utente non ha un tenant_id valido
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a valid tenant_id"
        )
    
    print(f"[TENANT] User {current_user.email} accessing tenant: {current_user.tenant_id}")
    return current_user.tenant_id

def with_tenant_filter(query, tenant_id: uuid.UUID):
    """
    Utility per applicare il filtro tenant_id a una query SQLModel.
    
    Args:
        query: Query SQLModel da filtrare
        tenant_id: UUID del tenant per il filtraggio
        
    Returns:
        Query filtrata per tenant_id
    """
    # Verifica se il modello ha il campo tenant_id
    if hasattr(query.column_descriptions[0]['entity'], 'tenant_id'):
        return query.filter(query.column_descriptions[0]['entity'].tenant_id == tenant_id)
    return query

def require_tenant_access(model_class):
    """
    Factory per creare dependency che verifica l'accesso al tenant.
    
    Args:
        model_class: Classe del modello da verificare
        
    Returns:
        Dependency function che verifica l'accesso al tenant
    """
    def tenant_checker(
        item_id: int,
        tenant_id: uuid.UUID = Depends(get_current_tenant),
        session: Session = Depends(get_session)
    ):
        # Verifica che l'item appartenga al tenant dell'utente
        query = select(model_class).where(
            model_class.id == item_id,
            model_class.tenant_id == tenant_id
        )
        result = safe_exec(session, query)
        item = result.first()
        
        if not item:
            print(f"[TENANT] Access denied: item {item_id} not found in tenant {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied"
            )
        
        print(f"[TENANT] Access granted: item {item_id} in tenant {tenant_id}")
        return item
    
    return tenant_checker

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

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Dependency opzionale per ottenere l'utente corrente.
    Restituisce None se non è fornito un token valido.
    
    Returns:
        Optional[User]: L'utente autenticato o None se non autenticato
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    # Try to get user from cache first
    cached_user = get_cached_user(email)
    if cached_user:
        return User(**cached_user)

    # If not in cache, get from database
    query = select(User).where(User.email == email)
    result = safe_exec(session, query)
    user = result.first()
    if user is None:
        return None

    # Cache the user for future requests
    cache_user(user, email)
    
    return user 