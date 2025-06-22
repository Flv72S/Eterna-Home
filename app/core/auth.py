from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_session
from app.models.user import User
from app.models.enums import UserRole
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
    user_service = UserService(session)
    auth_result = user_service.authenticate_user(username, password)
    if auth_result["error"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_result["user"]
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

def require_roles(required_roles: List[str], require_all: bool = False):
    """
    Dependency per verificare che l'utente abbia i ruoli richiesti.
    
    Args:
        required_roles: Lista dei ruoli richiesti
        require_all: Se True, l'utente deve avere tutti i ruoli. Se False, basta che ne abbia uno.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account utente disabilitato"
            )
        
        # Superuser ha sempre accesso
        if current_user.is_superuser:
            return current_user
        
        # Verifica ruoli
        if require_all:
            # L'utente deve avere tutti i ruoli richiesti
            for role in required_roles:
                if not current_user.has_role(role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Accesso negato. Ruolo richiesto: {role}"
                    )
        else:
            # L'utente deve avere almeno uno dei ruoli richiesti
            if not current_user.has_any_role(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Accesso negato. Ruoli richiesti: {', '.join(required_roles)}"
                )
        
        return current_user
    
    return role_checker

def require_admin():
    """Dependency per richiedere privilegi di amministratore"""
    return require_roles(UserRole.get_admin_roles())

def require_super_admin():
    """Dependency per richiedere privilegi di super amministratore"""
    return require_roles([UserRole.SUPER_ADMIN.value])

def require_professional():
    """Dependency per richiedere privilegi professionali"""
    return require_roles(UserRole.get_professional_roles())

def require_owner_or_admin():
    """Dependency per richiedere ruolo owner o admin."""
    return require_roles(["owner"] + UserRole.get_admin_roles())

def require_any_role():
    """Dependency per verificare che l'utente sia autenticato (qualsiasi ruolo)."""
    def any_role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account utente disabilitato"
            )
        return current_user
    
    return any_role_checker

def get_user_by_role(role: str, session: Session = Depends(get_session)) -> List[User]:
    """
    Utility per ottenere tutti gli utenti con un ruolo specifico.
    """
    statement = select(User).where(User.role == role, User.is_active == True)
    return session.exec(statement).all()

def get_users_by_roles(roles: List[str], session: Session = Depends(get_session)) -> List[User]:
    """
    Utility per ottenere tutti gli utenti con uno dei ruoli specificati.
    """
    statement = select(User).where(
        User.role.in_(roles),
        User.is_active == True
    )
    return session.exec(statement).all()

def can_user_access_resource(user: User, resource_owner_id: int) -> bool:
    """
    Verifica se un utente può accedere a una risorsa.
    
    Args:
        user: L'utente che richiede l'accesso
        resource_owner_id: ID del proprietario della risorsa
    
    Returns:
        True se l'utente può accedere alla risorsa
    """
    # L'utente può sempre accedere alle proprie risorse
    if user.id == resource_owner_id:
        return True
    
    # Gli amministratori possono accedere a tutte le risorse
    if user.can_access_admin_features():
        return True
    
    # I tecnici possono accedere alle risorse assegnate (logica specifica da implementare)
    if user.role == "technician":
        # I tecnici possono accedere solo a funzionalità di manutenzione
        return ["maintenance:read", "maintenance:write", "node:read"]
    
    if user.role == "manager":
        # I manager hanno accesso completo alle loro proprietà
        return ["house:read", "house:write", "room:read", "room:write", "booking:read", "booking:write"]
    
    return False

def require_resource_access(resource_owner_id: int):
    """
    Dependency per verificare l'accesso a una risorsa specifica.
    """
    def resource_checker(current_user: User = Depends(get_current_user)) -> User:
        if not can_user_access_resource(current_user, resource_owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accesso negato alla risorsa"
            )
        return current_user
    
    return resource_checker 