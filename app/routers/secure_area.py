"""
Router per testare il sistema di controllo ruoli con endpoint protetti.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.core.deps import require_roles, require_single_role, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/secure-area", tags=["secure-area"])

@router.get("/public")
async def public_endpoint():
    """Endpoint pubblico - accessibile a tutti gli utenti autenticati."""
    return {
        "message": "Public endpoint - accessible to all authenticated users",
        "access_level": "public"
    }

@router.get("/user-only")
async def user_only_endpoint(user: User = Depends(get_current_user)):
    """Endpoint per utenti autenticati - richiede solo autenticazione."""
    return {
        "message": "User-only endpoint - accessible to all authenticated users",
        "access_level": "user",
        "user_email": user.email,
        "user_roles": user.get_role_names()
    }

@router.get("/admin-only")
async def admin_only_endpoint(user: User = Depends(require_roles("admin", "super_admin"))):
    """Endpoint solo per admin e super admin."""
    return {
        "message": "Admin-only endpoint - accessible to admin and super_admin roles",
        "access_level": "admin",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "required_roles": ["admin", "super_admin"]
    }

@router.get("/super-admin-only")
async def super_admin_only_endpoint(user: User = Depends(require_single_role("super_admin"))):
    """Endpoint solo per super admin."""
    return {
        "message": "Super admin-only endpoint - accessible only to super_admin role",
        "access_level": "super_admin",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "required_role": "super_admin"
    }

@router.get("/technician-only")
async def technician_only_endpoint(user: User = Depends(require_roles("technician", "admin", "super_admin"))):
    """Endpoint per tecnici, admin e super admin."""
    return {
        "message": "Technician endpoint - accessible to technician, admin, and super_admin roles",
        "access_level": "technician",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "required_roles": ["technician", "admin", "super_admin"]
    }

@router.get("/owner-only")
async def owner_only_endpoint(user: User = Depends(require_roles("owner", "admin", "super_admin"))):
    """Endpoint per proprietari, admin e super admin."""
    return {
        "message": "Owner endpoint - accessible to owner, admin, and super_admin roles",
        "access_level": "owner",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "required_roles": ["owner", "admin", "super_admin"]
    }

@router.get("/user-info")
async def user_info_endpoint(user: User = Depends(get_current_user)):
    """Endpoint per ottenere informazioni dettagliate dell'utente corrente."""
    return {
        "message": "User information endpoint",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role": user.role,
            "all_roles": user.get_role_names(),
            "can_access_admin": user.can_access_admin_features(),
            "can_manage_users": user.can_manage_users(),
            "can_manage_roles": user.can_manage_roles()
        }
    }

@router.get("/role-test/{role_name}")
async def role_test_endpoint(
    role_name: str,
    user: User = Depends(get_current_user)
):
    """Endpoint dinamico per testare qualsiasi ruolo."""
    # Verifica manuale del ruolo
    if not user.has_role(role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {role_name}. User roles: {', '.join(user.get_role_names())}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "message": f"Role test endpoint for role: {role_name}",
        "access_level": "dynamic",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "required_role": role_name,
        "test_passed": True
    }

@router.get("/permissions")
async def permissions_endpoint(user: User = Depends(get_current_user)):
    """Endpoint per verificare i permessi dell'utente."""
    return {
        "message": "User permissions check",
        "user_email": user.email,
        "user_roles": user.get_role_names(),
        "permissions": {
            "can_access_admin_features": user.can_access_admin_features(),
            "can_manage_users": user.can_manage_users(),
            "can_manage_roles": user.can_manage_roles(),
            "has_admin_role": user.has_role("admin"),
            "has_super_admin_role": user.has_role("super_admin"),
            "has_technician_role": user.has_role("technician"),
            "has_owner_role": user.has_role("owner"),
            "has_any_admin_role": user.has_any_role(["admin", "super_admin"]),
            "has_any_technical_role": user.has_any_role(["technician", "admin", "super_admin"])
        }
    } 