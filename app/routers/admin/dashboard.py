from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
from app.core.auth import require_permission_in_tenant
from app.core.deps import get_current_tenant, get_db
from app.models.user import User
from app.models.role import Role
from app.models.house import House
from app.models.user_tenant_role import UserTenantRole
from app.models.user_house import UserHouse
from app.models.permission import Permission
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=None)
def admin_dashboard(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users"))
):
    """Dashboard principale amministrativa."""
    return templates.TemplateResponse("dashboard.html", {"request": request, "tenant_id": tenant_id})

@router.get("/users", response_class=None)
def admin_users(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """
    Recupera tutti gli utenti associati al tenant attivo con ruoli e conteggio case.
    Filtra per tenant_id per garantire isolamento multi-tenant.
    """
    # Query per utenti con ruoli nel tenant e conteggio case associate
    users_query = (
        select(
            User.id,
            User.username.label("name"),
            User.email,
            User.mfa_enabled,
            UserTenantRole.role,
            func.count(UserHouse.house_id).label("houses_count")
        )
        .outerjoin(UserTenantRole, (User.id == UserTenantRole.user_id) & (UserTenantRole.tenant_id == tenant_id))
        .outerjoin(UserHouse, (User.id == UserHouse.user_id) & (UserHouse.tenant_id == tenant_id) & (UserHouse.is_active == True))
        .where(UserTenantRole.tenant_id == tenant_id)
        .group_by(User.id, User.username, User.email, User.mfa_enabled, UserTenantRole.role)
        .order_by(User.username)
    )
    
    users_result = db.exec(users_query).all()
    
    # Formatta i risultati per il template
    users = []
    for user_row in users_result:
        users.append({
            "id": user_row.id,
            "name": user_row.name or "N/A",
            "email": user_row.email,
            "role": user_row.role or "N/A",
            "mfa_enabled": user_row.mfa_enabled,
            "houses_count": user_row.houses_count or 0
        })
    
    return templates.TemplateResponse("users.html", {
        "request": request, 
        "users": users, 
        "tenant_id": tenant_id
    })

@router.get("/roles", response_class=None)
def admin_roles(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """
    Recupera tutti i ruoli del tenant attivo con permessi associati e conteggio utenti.
    Filtra per tenant_id per garantire isolamento multi-tenant.
    """
    # Query per ruoli con conteggio utenti nel tenant
    roles_query = (
        select(
            Role.id,
            Role.name,
            Role.description,
            func.count(UserTenantRole.user_id).label("users_count")
        )
        .outerjoin(UserTenantRole, (Role.id == UserTenantRole.role) & (UserTenantRole.tenant_id == tenant_id))
        .where(Role.tenant_id == tenant_id)
        .group_by(Role.id, Role.name, Role.description)
        .order_by(Role.name)
    )
    
    roles_result = db.exec(roles_query).all()
    
    # Query per permessi associati ai ruoli
    permissions_query = (
        select(Permission.name, Permission.role_id)
        .where(Permission.tenant_id == tenant_id)
    )
    permissions_result = db.exec(permissions_query).all()
    
    # Crea mappa permessi per ruolo
    permissions_map = {}
    for perm in permissions_result:
        if perm.role_id not in permissions_map:
            permissions_map[perm.role_id] = []
        permissions_map[perm.role_id].append(perm.name)
    
    # Formatta i risultati per il template
    roles = []
    for role_row in roles_result:
        role_permissions = permissions_map.get(role_row.id, [])
        roles.append({
            "id": role_row.id,
            "name": role_row.name,
            "description": role_row.description,
            "permissions": role_permissions,
            "users_count": role_row.users_count or 0
        })
    
    return templates.TemplateResponse("roles.html", {
        "request": request, 
        "roles": roles, 
        "tenant_id": tenant_id
    })

@router.get("/houses", response_class=None)
def admin_houses(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """
    Recupera tutte le case del tenant attivo con conteggio utenti associati.
    Filtra per tenant_id per garantire isolamento multi-tenant.
    """
    # Query per case con conteggio utenti associati
    houses_query = (
        select(
            House.id,
            House.name,
            House.address,
            func.count(UserHouse.user_id).label("users_count")
        )
        .outerjoin(UserHouse, (House.id == UserHouse.house_id) & (UserHouse.tenant_id == tenant_id) & (UserHouse.is_active == True))
        .where(House.tenant_id == tenant_id)
        .group_by(House.id, House.name, House.address)
        .order_by(House.name)
    )
    
    houses_result = db.exec(houses_query).all()
    
    # Formatta i risultati per il template
    houses = []
    for house_row in houses_result:
        houses.append({
            "id": house_row.id,
            "name": house_row.name,
            "address": house_row.address,
            "users_count": house_row.users_count or 0
        })
    
    return templates.TemplateResponse("houses.html", {
        "request": request, 
        "houses": houses, 
        "tenant_id": tenant_id
    }) 