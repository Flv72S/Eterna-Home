"""
Router per la gestione degli utenti con supporto multi-tenant.
Integra RBAC e isolamento per tenant per gestione utenti sicura.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant
from app.models.user import User
from app.models.user_tenant_role import UserTenantRole
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserRead, UserResponse
from app.core.security import get_password_hash
from app.db.utils import safe_exec
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """
    Ottieni informazioni sull'utente corrente nel tenant attivo.
    """
    # Ottieni i ruoli dell'utente nel tenant corrente
    user_roles = current_user.get_roles_in_tenant(tenant_id)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        role=current_user.role,
        role_display=current_user.get_display_role(),
        tenant_id=str(tenant_id),
        tenant_roles=user_roles,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.get("/", response_model=List[UserRead])
async def get_users(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(10, ge=1, le=100, description="Numero massimo di record"),
    role: Optional[str] = Query(None, description="Filtra per ruolo nel tenant"),
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottieni lista degli utenti del tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Query base per utenti del tenant corrente
        base_query = select(User).join(UserTenantRole).where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        # Filtro per ruolo se specificato
        if role:
            base_query = base_query.where(UserTenantRole.role == role)
        
        # Paginazione
        query = base_query.offset(skip).limit(limit)
        
        # Esegui query
        users = safe_exec(session, query).all()
        
        # Converti in UserRead con informazioni tenant
        result = []
        for user in users:
            user_roles = user.get_roles_in_tenant(tenant_id)
            user_read = UserRead(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                role=user.role,
                role_display=user.get_display_role(),
                tenant_id=str(tenant_id),
                tenant_roles=user_roles,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            result.append(user_read)
        
        return result
        
    except Exception as e:
        print(f"[USERS] Errore durante listaggio utenti: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero degli utenti"
        )

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottieni statistiche sugli utenti del tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        from sqlmodel import func
        
        # Conta totale utenti nel tenant
        total_users_query = select(func.count(User.id)).join(UserTenantRole).where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        total_users = safe_exec(session, total_users_query).first()
        
        # Statistiche per ruolo nel tenant
        role_stats_query = select(
            UserTenantRole.role,
            func.count(UserTenantRole.user_id)
        ).where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        ).group_by(UserTenantRole.role)
        
        role_stats = safe_exec(session, role_stats_query).all()
        
        # Utenti attivi vs inattivi nel tenant
        active_users_query = select(func.count(User.id)).join(UserTenantRole).where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True,
            User.is_active == True
        )
        active_users = safe_exec(session, active_users_query).first()
        
        return {
            "tenant_id": str(tenant_id),
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": [
                {"role": role, "count": count} for role, count in role_stats
            ]
        }
        
    except Exception as e:
        print(f"[USERS] Errore durante recupero statistiche: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche"
        )

@router.get("/by-role/{role}")
async def get_users_by_role(
    role: str,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottieni tutti gli utenti con un ruolo specifico nel tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Query per utenti con ruolo specifico nel tenant
        query = select(User).join(UserTenantRole).where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.role == role,
            UserTenantRole.is_active == True
        )
        
        users = safe_exec(session, query).all()
        
        return {
            "tenant_id": str(tenant_id),
            "role": role,
            "count": len(users),
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "tenant_roles": user.get_roles_in_tenant(tenant_id)
                }
                for user in users
            ]
        }
        
    except Exception as e:
        print(f"[USERS] Errore durante recupero utenti per ruolo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero degli utenti per ruolo"
        )

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Crea un nuovo utente nel tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Crea l'utente con tenant_id
        user_data = user_create.dict()
        user_data["tenant_id"] = tenant_id
        user = UserService.create_user(session, user_create)
        
        # Assegna ruolo di default nel tenant
        default_role = "viewer"  # Ruolo di default per nuovi utenti
        UserTenantRole.add_user_to_tenant(
            session, user.id, tenant_id, default_role
        )
        
        # Ottieni i ruoli dell'utente nel tenant
        user_roles = user.get_roles_in_tenant(tenant_id)
        
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role,
            role_display=user.get_display_role(),
            tenant_id=str(tenant_id),
            tenant_roles=user_roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except Exception as e:
        print(f"[USERS] Errore durante creazione utente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la creazione dell'utente"
        )

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottieni un utente specifico del tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Query per utente specifico nel tenant
        query = select(User).join(UserTenantRole).where(
            User.id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        user = safe_exec(session, query).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato nel tenant corrente"
            )
        
        # Ottieni i ruoli dell'utente nel tenant
        user_roles = user.get_roles_in_tenant(tenant_id)
        
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role,
            role_display=user.get_display_role(),
            tenant_id=str(tenant_id),
            tenant_roles=user_roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USERS] Errore durante recupero utente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dell'utente"
        )

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un utente del tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Verifica che l'utente esista nel tenant
        query = select(User).join(UserTenantRole).where(
            User.id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        user = safe_exec(session, query).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato nel tenant corrente"
            )
        
        # Aggiorna i campi dell'utente
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Ottieni i ruoli dell'utente nel tenant
        user_roles = user.get_roles_in_tenant(tenant_id)
        
        return UserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role,
            role_display=user.get_display_role(),
            tenant_id=str(tenant_id),
            tenant_roles=user_roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USERS] Errore durante aggiornamento utente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento dell'utente"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Rimuovi un utente dal tenant corrente (non elimina l'utente, solo l'associazione).
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Verifica che l'utente esista nel tenant
        query = select(User).join(UserTenantRole).where(
            User.id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        user = safe_exec(session, query).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato nel tenant corrente"
            )
        
        # Rimuovi l'utente dal tenant (disattiva l'associazione)
        UserTenantRole.remove_user_from_tenant(session, user_id, tenant_id)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USERS] Errore durante rimozione utente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la rimozione dell'utente"
        )

@router.post("/{user_id}/assign-role")
async def assign_role_to_user(
    user_id: int,
    role: str,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Assegna un ruolo a un utente nel tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Verifica che l'utente esista nel tenant
        query = select(User).join(UserTenantRole).where(
            User.id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        user = safe_exec(session, query).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato nel tenant corrente"
            )
        
        # Assegna il ruolo
        UserTenantRole.add_user_to_tenant(session, user_id, tenant_id, role)
        
        return {
            "message": f"Ruolo '{role}' assegnato con successo all'utente",
            "user_id": user_id,
            "tenant_id": str(tenant_id),
            "role": role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USERS] Errore durante assegnazione ruolo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'assegnazione del ruolo"
        )

@router.delete("/{user_id}/remove-role/{role}")
async def remove_role_from_user(
    user_id: int,
    role: str,
    current_user: User = Depends(require_permission_in_tenant("manage_users")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Rimuovi un ruolo specifico da un utente nel tenant corrente.
    Richiede permesso 'manage_users' nel tenant attivo.
    """
    try:
        # Verifica che l'utente esista nel tenant
        query = select(User).join(UserTenantRole).where(
            User.id == user_id,
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.is_active == True
        )
        
        user = safe_exec(session, query).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato nel tenant corrente"
            )
        
        # Rimuovi il ruolo specifico
        UserTenantRole.remove_user_from_tenant(session, user_id, tenant_id)
        
        return {
            "message": f"Ruolo '{role}' rimosso con successo dall'utente",
            "user_id": user_id,
            "tenant_id": str(tenant_id),
            "role": role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USERS] Errore durante rimozione ruolo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la rimozione del ruolo"
        )

@router.get("/roles/list")
async def get_available_roles(
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant)
):
    """
    Ottieni la lista dei ruoli disponibili nel tenant corrente.
    """
    # Ruoli disponibili per il tenant
    available_roles = [
        {"value": "admin", "display": "Amministratore"},
        {"value": "manager", "display": "Manager"},
        {"value": "editor", "display": "Editor"},
        {"value": "viewer", "display": "Visualizzatore"},
        {"value": "technician", "display": "Tecnico"},
        {"value": "designer", "display": "Progettista"}
    ]
    
    return {
        "tenant_id": str(tenant_id),
        "available_roles": available_roles
    }

# TODO: Implementare endpoint per gestione ruoli avanzata
# TODO: Aggiungere endpoint per trasferimento utenti tra tenant
# TODO: Implementare audit trail per modifiche utenti
# TODO: Aggiungere endpoint per bulk operations 