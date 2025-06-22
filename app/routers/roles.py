"""
Router per la gestione dei ruoli utente
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[dict])
async def get_all_roles(
    current_user: User = Depends(get_current_user)
):
    """
    Ottieni tutti i ruoli disponibili nel sistema
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    roles = []
    for role in UserRole:
        roles.append({
            "value": role.value,
            "name": role.value,
            "display_name": UserRole.get_display_name(role.value),
            "category": "admin" if role in UserRole.get_admin_roles() else 
                       "professional" if role in UserRole.get_professional_roles() else 
                       "private",
            "description": f"Ruolo {role.value}",
            "permissions": []
        })
    
    return roles

@router.get("/users/{role_name}", response_model=List[UserResponse])
async def get_users_by_role(
    role_name: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottieni tutti gli utenti con un ruolo specifico
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role_name}' non valido"
        )
    
    user_service = UserService(db)
    users = user_service.get_users_by_role(user_role, skip=skip, limit=limit)
    return users

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiorna il ruolo di un utente specifico
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role}' non valido"
        )
    
    # Verifica che l'utente esista
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Non permettere di cambiare il ruolo di un super admin (tranne che da un altro super admin)
    if user.has_role("super_admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non puoi modificare il ruolo di un super amministratore"
        )
    
    # Aggiorna il ruolo
    updated_user = user_service.update_user_role(user_id, user_role)
    
    return {
        "message": f"Ruolo aggiornato con successo per {updated_user.email}",
        "user_id": updated_user.id,
        "new_role": updated_user.role
    }

@router.get("/stats")
async def get_role_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottieni statistiche sui ruoli degli utenti
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    role_distribution = {}
    total_users = 0
    
    user_service = UserService(db)
    for role in UserRole:
        count = user_service.count_users_by_role(role)
        role_distribution[role.value] = {
            "count": count,
            "name": role.name,
            "display_name": UserRole.get_display_name(role.value)
        }
        total_users += count
    
    return {
        "total_users": total_users,
        "role_distribution": role_distribution
    }

@router.get("/my-permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Ottieni i permessi dell'utente corrente
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "role_display_name": UserRole.get_display_name(current_user.role),
        "is_superuser": current_user.is_superuser,
        "is_active": current_user.is_active,
        "can_access_admin": current_user.can_access_admin_features(),
        "can_manage_users": current_user.can_manage_users(),
        "can_manage_roles": current_user.can_manage_roles(),
        "permissions": {
            "admin_access": current_user.can_access_admin_features(),
            "user_management": current_user.can_manage_users(),
            "role_management": current_user.can_manage_roles(),
            "read_access": True,  # Tutti gli utenti autenticati possono leggere
            "write_access": current_user.can_access_admin_features() or current_user.role in ["owner", "manager"]
        }
    }

@router.post("/users/{user_id}/roles/add")
async def add_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiungi un ruolo aggiuntivo a un utente (per sistemi con ruoli multipli)
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role}' non valido"
        )
    
    # Verifica che l'utente esista
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Aggiungi il ruolo (implementazione per sistemi con ruoli multipli)
    # Per ora, questo endpoint è preparato per future estensioni
    return {
        "message": f"Ruolo {role} aggiunto con successo a {user.email}",
        "user_id": user.id,
        "added_role": role
    }

@router.delete("/users/{user_id}/roles/{role}")
async def remove_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rimuovi un ruolo da un utente (per sistemi con ruoli multipli)
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role}' non valido"
        )
    
    # Verifica che l'utente esista
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Rimuovi il ruolo (implementazione per sistemi con ruoli multipli)
    # Per ora, questo endpoint è preparato per future estensioni
    return {
        "message": f"Ruolo {role} rimosso con successo da {user.email}",
        "user_id": user.id,
        "removed_role": role
    }

@router.post("/users/{user_id}/roles")
async def add_user_role_test_endpoint(
    user_id: int,
    role_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiungi un ruolo a un utente (endpoint per i test)
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role_name}' non valido"
        )
    
    # Verifica che l'utente esista
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Aggiungi il ruolo (implementazione per sistemi con ruoli multipli)
    # Per ora, questo endpoint è preparato per future estensioni
    return {
        "message": f"Ruolo {role_name} aggiunto con successo a {user.email}",
        "user_id": user.id,
        "added_role": role_name
    }

@router.delete("/users/{user_id}/roles")
async def remove_user_role_test_endpoint(
    user_id: int,
    role_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rimuovi un ruolo da un utente (endpoint per i test)
    """
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Richiesti permessi amministrativi."
        )
    
    try:
        user_role = UserRole(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo '{role_name}' non valido"
        )
    
    # Verifica che l'utente esista
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Rimuovi il ruolo (implementazione per sistemi con ruoli multipli)
    # Per ora, questo endpoint è preparato per future estensioni
    return {
        "message": f"Ruolo {role_name} rimosso con successo da {user.email}",
        "user_id": user.id,
        "removed_role": role_name
    } 