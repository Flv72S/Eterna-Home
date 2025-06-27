"""
Sistema RBAC (Role-Based Access Control) Multi-Tenant centralizzato.
Fornisce decoratori e dependency per gestire autorizzazioni granulari
in contesto multi-tenant.
"""

from typing import List, Optional, Union
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
import uuid
from functools import wraps

from app.core.deps import get_current_user, get_current_tenant
from app.models.user import User
from app.models.user_tenant_role import UserTenantRole
from app.db.session import get_session
from app.db.utils import safe_exec

def require_role_in_tenant(required_role: str):
    """
    Dependency factory per verificare che l'utente abbia un ruolo specifico nel tenant attivo.
    
    Args:
        required_role: Ruolo richiesto nel tenant attivo
    
    Returns:
        Dependency function che verifica il ruolo dell'utente nel tenant
    
    Example:
        @app.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role_in_tenant("admin"))):
            return {"message": "Admin access granted"}
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        tenant_id: uuid.UUID = Depends(get_current_tenant),
        session: Session = Depends(get_session)
    ) -> User:
        # Verifica se l'utente ha il ruolo richiesto nel tenant attivo
        if not current_user.has_role_in_tenant(required_role, tenant_id):
            # Log del tentativo di accesso non autorizzato
            print(f"[RBAC] Access denied for user {current_user.email} "
                  f"to tenant {tenant_id} requiring role: {required_role}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role '{required_role}' in current tenant. "
                       f"User roles in tenant: {current_user.get_roles_in_tenant(tenant_id)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log dell'accesso autorizzato
        print(f"[RBAC] Access granted for user {current_user.email} "
              f"to tenant {tenant_id} with role: {required_role}")
        
        return current_user
    
    return role_checker

def require_any_role_in_tenant(required_roles: List[str]):
    """
    Dependency factory per verificare che l'utente abbia almeno uno dei ruoli specificati nel tenant attivo.
    
    Args:
        required_roles: Lista di ruoli richiesti (almeno uno)
    
    Returns:
        Dependency function che verifica i ruoli dell'utente nel tenant
    
    Example:
        @app.get("/editor-or-admin")
        def editor_or_admin_endpoint(user: User = Depends(require_any_role_in_tenant(["editor", "admin"]))):
            return {"message": "Editor or admin access granted"}
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        tenant_id: uuid.UUID = Depends(get_current_tenant),
        session: Session = Depends(get_session)
    ) -> User:
        # Verifica se l'utente ha almeno uno dei ruoli richiesti nel tenant attivo
        if not current_user.has_any_role_in_tenant(required_roles, tenant_id):
            # Log del tentativo di accesso non autorizzato
            print(f"[RBAC] Access denied for user {current_user.email} "
                  f"to tenant {tenant_id} requiring roles: {required_roles}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of roles {required_roles} in current tenant. "
                       f"User roles in tenant: {current_user.get_roles_in_tenant(tenant_id)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log dell'accesso autorizzato
        print(f"[RBAC] Access granted for user {current_user.email} "
              f"to tenant {tenant_id} with roles: {required_roles}")
        
        return current_user
    
    return role_checker

def require_permission_in_tenant(permission: str):
    """
    Dependency factory per verificare che l'utente abbia un permesso specifico nel tenant attivo.
    I permessi sono mappati ai ruoli tramite una logica di business.
    
    Args:
        permission: Permesso richiesto (es. "read_documents", "write_documents", "delete_documents")
    
    Returns:
        Dependency function che verifica il permesso dell'utente nel tenant
    
    Example:
        @app.get("/documents")
        def read_documents(user: User = Depends(require_permission_in_tenant("read_documents"))):
            return {"message": "Documents read access granted"}
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        tenant_id: uuid.UUID = Depends(get_current_tenant),
        session: Session = Depends(get_session)
    ) -> User:
        # Mappa permessi ai ruoli (logica di business)
        permission_role_map = {
            "read_documents": ["viewer", "editor", "admin", "super_admin"],
            "write_documents": ["editor", "admin", "super_admin"],
            "delete_documents": ["admin", "super_admin"],
            "manage_users": ["admin", "super_admin"],
            "manage_roles": ["super_admin"],
            "read_bim_models": ["viewer", "editor", "admin", "super_admin"],
            "write_bim_models": ["editor", "admin", "super_admin"],
            "delete_bim_models": ["admin", "super_admin"],
            "upload_bim": ["editor", "admin", "super_admin"],
            "read_audio_logs": ["viewer", "editor", "admin", "super_admin"],
            "write_audio_logs": ["editor", "admin", "super_admin"],
            "delete_audio_logs": ["admin", "super_admin"],
            "manage_voice_logs": ["admin", "super_admin"],
            "submit_voice": ["viewer", "editor", "admin", "super_admin"],
            "read_voice_logs": ["viewer", "editor", "admin", "super_admin"],
            "manage_house_access": ["admin", "super_admin"],
            "read_house_access": ["viewer", "editor", "admin", "super_admin"],
            "write_house_access": ["editor", "admin", "super_admin"],
        }
        
        # Ottieni i ruoli richiesti per il permesso
        required_roles = permission_role_map.get(permission, [])
        
        if not required_roles:
            print(f"[RBAC] Unknown permission: {permission}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission: {permission}"
            )
        
        # Verifica se l'utente ha almeno uno dei ruoli richiesti nel tenant attivo
        if not current_user.has_any_role_in_tenant(required_roles, tenant_id):
            # Log del tentativo di accesso non autorizzato
            print(f"[RBAC] Access denied for user {current_user.email} "
                  f"to tenant {tenant_id} requiring permission: {permission}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission '{permission}' in current tenant. "
                       f"User roles in tenant: {current_user.get_roles_in_tenant(tenant_id)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log dell'accesso autorizzato
        print(f"[RBAC] Access granted for user {current_user.email} "
              f"to tenant {tenant_id} with permission: {permission}")
        
        return current_user
    
    return permission_checker

def require_any_permission_in_tenant(permissions: List[str]):
    """
    Dependency factory per verificare che l'utente abbia almeno uno dei permessi specificati nel tenant attivo.
    
    Args:
        permissions: Lista di permessi richiesti (almeno uno)
    
    Returns:
        Dependency function che verifica i permessi dell'utente nel tenant
    
    Example:
        @app.get("/documents")
        def read_documents(user: User = Depends(require_any_permission_in_tenant(["read_documents", "write_documents"]))):
            return {"message": "Document access granted"}
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        tenant_id: uuid.UUID = Depends(get_current_tenant),
        session: Session = Depends(get_session)
    ) -> User:
        # Mappa permessi ai ruoli (logica di business)
        permission_role_map = {
            "read_documents": ["viewer", "editor", "admin", "super_admin"],
            "write_documents": ["editor", "admin", "super_admin"],
            "delete_documents": ["admin", "super_admin"],
            "manage_users": ["admin", "super_admin"],
            "manage_roles": ["super_admin"],
            "read_bim_models": ["viewer", "editor", "admin", "super_admin"],
            "write_bim_models": ["editor", "admin", "super_admin"],
            "delete_bim_models": ["admin", "super_admin"],
            "upload_bim": ["editor", "admin", "super_admin"],
            "read_audio_logs": ["viewer", "editor", "admin", "super_admin"],
            "write_audio_logs": ["editor", "admin", "super_admin"],
            "delete_audio_logs": ["admin", "super_admin"],
            "manage_voice_logs": ["admin", "super_admin"],
            "submit_voice": ["viewer", "editor", "admin", "super_admin"],
            "read_voice_logs": ["viewer", "editor", "admin", "super_admin"],
            "manage_house_access": ["admin", "super_admin"],
            "read_house_access": ["viewer", "editor", "admin", "super_admin"],
            "write_house_access": ["editor", "admin", "super_admin"],
        }
        
        # Ottieni tutti i ruoli richiesti per i permessi
        all_required_roles = set()
        for permission in permissions:
            required_roles = permission_role_map.get(permission, [])
            all_required_roles.update(required_roles)
        
        if not all_required_roles:
            print(f"[RBAC] Unknown permissions: {permissions}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permissions: {permissions}"
            )
        
        # Verifica se l'utente ha almeno uno dei ruoli richiesti nel tenant attivo
        if not current_user.has_any_role_in_tenant(list(all_required_roles), tenant_id):
            # Log del tentativo di accesso non autorizzato
            print(f"[RBAC] Access denied for user {current_user.email} "
                  f"to tenant {tenant_id} requiring permissions: {permissions}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of permissions {permissions} in current tenant. "
                       f"User roles in tenant: {current_user.get_roles_in_tenant(tenant_id)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log dell'accesso autorizzato
        print(f"[RBAC] Access granted for user {current_user.email} "
              f"to tenant {tenant_id} with permissions: {permissions}")
        
        return current_user
    
    return permission_checker

def get_user_tenant_roles(
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
) -> List[str]:
    """
    Dependency per ottenere i ruoli dell'utente nel tenant attivo.
    
    Returns:
        Lista dei ruoli dell'utente nel tenant attivo
    """
    return current_user.get_roles_in_tenant(tenant_id)

def get_user_tenants(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> List[uuid.UUID]:
    """
    Dependency per ottenere tutti i tenant a cui l'utente è associato.
    
    Returns:
        Lista degli ID dei tenant a cui l'utente è associato
    """
    return current_user.get_tenant_ids()

# Alias per compatibilità
require_role = require_role_in_tenant
require_roles = require_any_role_in_tenant
require_permission = require_permission_in_tenant
require_permissions = require_any_permission_in_tenant

def require_house_access(house_id_param: str = "house_id"):
    """
    Decoratore per verificare che l'utente abbia accesso a una casa specifica.
    
    Args:
        house_id_param: Nome del parametro che contiene l'ID della casa
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Estrai house_id dai parametri
            house_id = kwargs.get(house_id_param)
            if house_id is None:
                # Prova a cercare nei parametri posizionali
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                try:
                    house_id_idx = param_names.index(house_id_param)
                    if house_id_idx < len(args):
                        house_id = args[house_id_idx]
                except ValueError:
                    pass
            
            if house_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parametro {house_id_param} mancante"
                )
            
            # Ottieni utente e tenant corrente
            current_user = kwargs.get('current_user')
            tenant_id = kwargs.get('tenant_id')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Utente non autenticato"
                )
            
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant ID mancante"
                )
            
            # Verifica accesso alla casa
            if not current_user.has_house_access(house_id, tenant_id):
                logger.warning(
                    "Tentativo di accesso non autorizzato a casa",
                    extra={
                        "user_id": current_user.id,
                        "house_id": house_id,
                        "tenant_id": tenant_id,
                        "endpoint": func.__name__
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non hai accesso a questa casa"
                )
            
            logger.info(
                "Accesso a casa verificato",
                extra={
                    "user_id": current_user.id,
                    "house_id": house_id,
                    "tenant_id": tenant_id,
                    "endpoint": func.__name__
                }
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 