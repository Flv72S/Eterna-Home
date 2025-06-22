from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.utils.security import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserRead, UserResponse
from app.core.security import get_password_hash
from app.core.deps import get_session
from app.db.utils import safe_exec
from app.services.user import UserService
from app.core.auth import require_admin, require_super_admin, require_any_role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Ottieni informazioni sull'utente corrente.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        role=current_user.role,
        role_display=current_user.get_display_role(),
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.get("/", response_model=List[UserRead])
async def get_users(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(10, ge=1, le=100, description="Numero massimo di record"),
    role: Optional[str] = Query(None, description="Filtra per ruolo"),
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni lista degli utenti (solo amministratori).
    """
    user_service = UserService(session)
    
    if role:
        # Valida il ruolo
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ruolo non valido. Ruoli validi: {', '.join(valid_roles)}"
            )
        users = user_service.get_users_by_role(role)
    else:
        users = user_service.get_users(skip=skip, limit=limit)
    
    # Converti in UserRead con role_display
    result = []
    for user in users:
        user_read = UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role,
            role_display=user.get_display_role(),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        result.append(user_read)
    
    return result

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni statistiche sugli utenti (solo amministratori).
    """
    user_service = UserService(session)
    return user_service.get_user_stats()

@router.get("/by-role/{role}")
async def get_users_by_role(
    role: str,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni tutti gli utenti con un ruolo specifico (solo amministratori).
    """
    # Valida il ruolo
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo non valido. Ruoli validi: {', '.join(valid_roles)}"
        )
    
    user_service = UserService(session)
    users = user_service.get_users_by_role(role)
    
    return {
        "role": role,
        "display_name": UserRole.get_display_name(role),
        "count": len(users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active
            }
            for user in users
        ]
    }

@router.get("/admin")
async def get_admin_users(
    current_user: User = Depends(require_super_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni tutti gli utenti amministratori (solo super admin).
    """
    user_service = UserService(session)
    admin_users = user_service.get_admin_users()
    
    return {
        "count": len(admin_users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "role_display": user.get_display_role()
            }
            for user in admin_users
        ]
    }

@router.get("/professional")
async def get_professional_users(
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni tutti gli utenti con ruoli professionali (solo amministratori).
    """
    user_service = UserService(session)
    users = user_service.get_professional_users()
    
    return {
        "count": len(users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "role_display": user.get_display_role()
            }
            for user in users
        ]
    }

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Crea un nuovo utente (solo amministratori).
    """
    user_service = UserService(session)
    user = user_service.create_user(user_create)
    
    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        role_display=user.get_display_role(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Ottieni un utente specifico (solo amministratori).
    """
    user_service = UserService(session)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        role_display=user.get_display_role(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin()),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un utente (solo amministratori).
    """
    user_service = UserService(session)
    user = user_service.update_user(user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    return UserRead(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        role_display=user.get_display_role(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_super_admin()),
    session: Session = Depends(get_session)
):
    """
    Elimina un utente (solo super admin).
    """
    user_service = UserService(session)
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    return None

@router.get("/roles/list")
async def get_available_roles(
    current_user: User = Depends(require_any_role())
):
    """
    Ottieni la lista di tutti i ruoli disponibili.
    """
    roles = []
    for role in UserRole:
        roles.append({
            "value": role.value,
            "display_name": role.get_display_name(role.value),
            "category": "admin" if role.value in UserRole.get_admin_roles() else
                       "professional" if role.value in UserRole.get_professional_roles() else
                       "private"
        })
    
    return {
        "roles": roles,
        "default_role": UserRole.get_default_role(),
        "admin_roles": UserRole.get_admin_roles(),
        "professional_roles": UserRole.get_professional_roles(),
        "private_roles": UserRole.get_private_roles()
    } 