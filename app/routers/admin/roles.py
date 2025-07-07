"""
Router per la gestione amministrativa dei ruoli e permessi.
Implementa CRUD completo per ruoli, gestione permessi e assegnazione utenti.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, func
import uuid

from app.core.auth import require_permission_in_tenant
from app.core.deps import get_current_tenant, get_db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission, RolePermission
from app.models.user_tenant_role import UserTenantRole
from app.models.house import House
from app.models.user_house import UserHouse
from app.services.mfa_service import MFAService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
mfa_service = MFAService()

@router.get("/roles", response_class=None)
def admin_roles_list(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Lista tutti i ruoli del tenant attivo."""
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
    
    return templates.TemplateResponse("roles/list.html", {
        "request": request, 
        "roles": roles, 
        "tenant_id": tenant_id
    })

@router.get("/roles/new", response_class=None)
def admin_roles_new_form(
    request: Request, 
    tenant_id: uuid.UUID = Depends(get_current_tenant), 
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Form per la creazione di un nuovo ruolo."""
    available_permissions = [
        {"name": "read_documents", "description": "Lettura documenti"},
        {"name": "write_documents", "description": "Scrittura documenti"},
        {"name": "delete_documents", "description": "Eliminazione documenti"},
        {"name": "upload_documents", "description": "Upload documenti"},
        {"name": "read_bim_models", "description": "Lettura modelli BIM"},
        {"name": "write_bim_models", "description": "Scrittura modelli BIM"},
        {"name": "delete_bim_models", "description": "Eliminazione modelli BIM"},
        {"name": "upload_bim", "description": "Upload modelli BIM"},
        {"name": "manage_bim_sources", "description": "Gestione fonti BIM pubbliche"},
        {"name": "read_audio_logs", "description": "Lettura log audio"},
        {"name": "write_audio_logs", "description": "Scrittura log audio"},
        {"name": "delete_audio_logs", "description": "Eliminazione log audio"},
        {"name": "manage_voice_logs", "description": "Gestione log vocali"},
        {"name": "submit_voice", "description": "Invio comandi vocali"},
        {"name": "read_voice_logs", "description": "Lettura log vocali"},
        {"name": "manage_house_access", "description": "Gestione accessi case"},
        {"name": "read_house_access", "description": "Lettura accessi case"},
        {"name": "write_house_access", "description": "Scrittura accessi case"},
        {"name": "manage_users", "description": "Gestione utenti"},
        {"name": "manage_roles", "description": "Gestione ruoli"},
        {"name": "read_logs", "description": "Lettura log sistema"},
        {"name": "write_logs", "description": "Scrittura log sistema"},
        {"name": "view_monitoring", "description": "Visualizza monitoraggio sistema"},
        {"name": "admin_access", "description": "Accesso amministrativo"}
    ]
    
    return templates.TemplateResponse("roles/new.html", {
        "request": request,
        "tenant_id": tenant_id,
        "available_permissions": available_permissions
    })

@router.post("/roles/new", response_class=None)
async def admin_roles_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    permissions: List[str] = Form([]),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Crea un nuovo ruolo con i permessi specificati."""
    try:
        # Verifica se il ruolo esiste già
        existing_role = db.exec(
            select(Role).where(Role.name == name, Role.tenant_id == tenant_id)
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ruolo '{name}' già esistente nel tenant"
            )
        
        # Crea il nuovo ruolo
        new_role = Role(
            name=name,
            description=description,
            tenant_id=tenant_id
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        # Aggiungi i permessi al ruolo
        for permission_name in permissions:
            # Crea o recupera il permesso
            permission = db.exec(
                select(Permission).where(
                    Permission.name == permission_name,
                    Permission.tenant_id == tenant_id
                )
            ).first()
            
            if not permission:
                permission = Permission(
                    name=permission_name,
                    description=f"Permesso {permission_name}",
                    tenant_id=tenant_id
                )
                db.add(permission)
                db.commit()
                db.refresh(permission)
            
            # Crea l'associazione ruolo-permesso
            role_permission = RolePermission(
                role_id=new_role.id,
                permission_id=permission.id
            )
            db.add(role_permission)
        
        db.commit()
        return RedirectResponse(url="/admin/roles", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione del ruolo: {str(e)}"
        )

@router.get("/roles/{role_id}/edit", response_class=None)
def admin_roles_edit_form(
    request: Request,
    role_id: int,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Form per la modifica di un ruolo esistente."""
    # Recupera il ruolo
    role = db.exec(
        select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruolo non trovato"
        )
    
    # Recupera i permessi del ruolo
    role_permissions = db.exec(
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
    ).all()
    
    role_permission_names = [p.name for p in role_permissions]
    
    # Lista permessi disponibili
    available_permissions = [
        {"name": "read_documents", "description": "Lettura documenti"},
        {"name": "write_documents", "description": "Scrittura documenti"},
        {"name": "delete_documents", "description": "Eliminazione documenti"},
        {"name": "upload_documents", "description": "Upload documenti"},
        {"name": "read_bim_models", "description": "Lettura modelli BIM"},
        {"name": "write_bim_models", "description": "Scrittura modelli BIM"},
        {"name": "delete_bim_models", "description": "Eliminazione modelli BIM"},
        {"name": "upload_bim", "description": "Upload modelli BIM"},
        {"name": "manage_bim_sources", "description": "Gestione fonti BIM pubbliche"},
        {"name": "read_audio_logs", "description": "Lettura log audio"},
        {"name": "write_audio_logs", "description": "Scrittura log audio"},
        {"name": "delete_audio_logs", "description": "Eliminazione log audio"},
        {"name": "manage_voice_logs", "description": "Gestione log vocali"},
        {"name": "submit_voice", "description": "Invio comandi vocali"},
        {"name": "read_voice_logs", "description": "Lettura log vocali"},
        {"name": "manage_house_access", "description": "Gestione accessi case"},
        {"name": "read_house_access", "description": "Lettura accessi case"},
        {"name": "write_house_access", "description": "Scrittura accessi case"},
        {"name": "manage_users", "description": "Gestione utenti"},
        {"name": "manage_roles", "description": "Gestione ruoli"},
        {"name": "read_logs", "description": "Lettura log sistema"},
        {"name": "write_logs", "description": "Scrittura log sistema"},
        {"name": "view_monitoring", "description": "Visualizza monitoraggio sistema"},
        {"name": "admin_access", "description": "Accesso amministrativo"}
    ]
    
    return templates.TemplateResponse("roles/edit.html", {
        "request": request,
        "role": role,
        "role_permissions": role_permission_names,
        "available_permissions": available_permissions,
        "tenant_id": tenant_id
    })

@router.post("/roles/{role_id}/edit", response_class=None)
async def admin_roles_update(
    request: Request,
    role_id: int,
    name: str = Form(...),
    description: str = Form(...),
    permissions: List[str] = Form([]),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Aggiorna un ruolo esistente."""
    try:
        # Recupera il ruolo
        role = db.exec(
            select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ruolo non trovato"
            )
        
        # Verifica se il nome è già usato da un altro ruolo
        existing_role = db.exec(
            select(Role).where(
                Role.name == name, 
                Role.tenant_id == tenant_id,
                Role.id != role_id
            )
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ruolo '{name}' già esistente nel tenant"
            )
        
        # Aggiorna il ruolo
        role.name = name
        role.description = description
        db.add(role)
        
        # Rimuovi tutti i permessi esistenti
        db.exec(
            select(RolePermission).where(RolePermission.role_id == role_id)
        ).delete()
        
        # Aggiungi i nuovi permessi
        for permission_name in permissions:
            # Crea o recupera il permesso
            permission = db.exec(
                select(Permission).where(
                    Permission.name == permission_name,
                    Permission.tenant_id == tenant_id
                )
            ).first()
            
            if not permission:
                permission = Permission(
                    name=permission_name,
                    description=f"Permesso {permission_name}",
                    tenant_id=tenant_id
                )
                db.add(permission)
                db.commit()
                db.refresh(permission)
            
            # Crea l'associazione ruolo-permesso
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission.id
            )
            db.add(role_permission)
        
        db.commit()
        return RedirectResponse(url="/admin/roles", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'aggiornamento del ruolo: {str(e)}"
        )

@router.post("/roles/{role_id}/delete", response_class=None)
async def admin_roles_delete(
    request: Request,
    role_id: int,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Elimina un ruolo (solo se non ha utenti associati)."""
    try:
        # Recupera il ruolo
        role = db.exec(
            select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ruolo non trovato"
            )
        
        # Verifica se ci sono utenti associati
        users_count = db.exec(
            select(func.count(UserTenantRole.user_id))
            .where(UserTenantRole.role == role.name, UserTenantRole.tenant_id == tenant_id)
        ).first()
        
        if users_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile eliminare il ruolo: {users_count} utenti associati"
            )
        
        # Rimuovi le associazioni ruolo-permesso
        db.exec(
            select(RolePermission).where(RolePermission.role_id == role_id)
        ).delete()
        
        # Elimina il ruolo
        db.delete(role)
        db.commit()
        
        return RedirectResponse(url="/admin/roles", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'eliminazione del ruolo: {str(e)}"
        )

@router.get("/roles/assign", response_class=None)
def admin_roles_assign_form(
    request: Request,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Form per l'assegnazione di ruoli agli utenti."""
    # Recupera tutti gli utenti del tenant
    users_query = (
        select(User.id, User.username, User.email)
        .join(UserTenantRole, User.id == UserTenantRole.user_id)
        .where(UserTenantRole.tenant_id == tenant_id)
        .order_by(User.username)
    )
    users = db.exec(users_query).all()
    
    # Recupera tutti i ruoli del tenant
    roles = db.exec(
        select(Role).where(Role.tenant_id == tenant_id).order_by(Role.name)
    ).all()
    
    # Recupera tutte le case del tenant
    houses = db.exec(
        select(House).where(House.tenant_id == tenant_id).order_by(House.name)
    ).all()
    
    return templates.TemplateResponse("roles/assign.html", {
        "request": request,
        "users": users,
        "roles": roles,
        "houses": houses,
        "tenant_id": tenant_id
    })

@router.post("/roles/assign", response_class=None)
async def admin_roles_assign(
    request: Request,
    user_id: int = Form(...),
    role_id: int = Form(...),
    house_id: Optional[int] = Form(None),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Assegna un ruolo a un utente nel tenant."""
    try:
        # Recupera l'utente
        user_obj = db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        # Recupera il ruolo
        role = db.exec(
            select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ruolo non trovato"
            )
        
        # Assegna il ruolo all'utente nel tenant
        UserTenantRole.add_user_to_tenant(db, user_id, tenant_id, role.name)
        
        # Se è specificata una casa, assegna anche l'utente alla casa
        if house_id:
            house = db.exec(
                select(House).where(House.id == house_id, House.tenant_id == tenant_id)
            ).first()
            
            if house:
                # Verifica se l'associazione esiste già
                existing_house_association = db.exec(
                    select(UserHouse).where(
                        UserHouse.user_id == user_id,
                        UserHouse.house_id == house_id,
                        UserHouse.tenant_id == tenant_id
                    )
                ).first()
                
                if not existing_house_association:
                    user_house = UserHouse(
                        user_id=user_id,
                        house_id=house_id,
                        tenant_id=tenant_id,
                        role_in_house=role.name
                    )
                    db.add(user_house)
                    db.commit()
        
        return RedirectResponse(url="/admin/roles", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'assegnazione del ruolo: {str(e)}"
        )

@router.get("/mfa", response_class=None)
def admin_mfa_management(
    request: Request,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Gestione MFA per utenti privilegiati."""
    # Recupera utenti con ruoli privilegiati (admin, super_admin)
    privileged_users_query = (
        select(
            User.id,
            User.username,
            User.email,
            User.mfa_enabled,
            UserTenantRole.role
        )
        .join(UserTenantRole, User.id == UserTenantRole.user_id)
        .where(
            UserTenantRole.tenant_id == tenant_id,
            UserTenantRole.role.in_(["admin", "super_admin"])
        )
        .order_by(User.username)
    )
    
    privileged_users = db.exec(privileged_users_query).all()
    
    users = []
    for user_row in privileged_users:
        users.append({
            "id": user_row.id,
            "username": user_row.username,
            "email": user_row.email,
            "mfa_enabled": user_row.mfa_enabled,
            "role": user_row.role
        })
    
    return templates.TemplateResponse("roles/mfa.html", {
        "request": request,
        "users": users,
        "tenant_id": tenant_id
    })

@router.post("/mfa/{user_id}/setup", response_class=None)
async def admin_mfa_setup(
    request: Request,
    user_id: int,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Setup MFA per un utente privilegiato."""
    try:
        # Recupera l'utente
        target_user = db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        # Verifica che l'utente abbia un ruolo privilegiato nel tenant
        has_privileged_role = db.exec(
            select(UserTenantRole).where(
                UserTenantRole.user_id == user_id,
                UserTenantRole.tenant_id == tenant_id,
                UserTenantRole.role.in_(["admin", "super_admin"])
            )
        ).first()
        
        if not has_privileged_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="L'utente non ha un ruolo privilegiato"
            )
        
        # Setup MFA
        setup_data = mfa_service.setup_mfa(target_user)
        
        # Aggiorna l'utente con il segreto MFA
        target_user.mfa_secret = setup_data["secret"]
        db.add(target_user)
        db.commit()
        
        return {
            "message": "MFA setup completato",
            "secret": setup_data["secret"],
            "qr_code": setup_data["qr_code"],
            "backup_codes": setup_data["backup_codes"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il setup MFA: {str(e)}"
        )

@router.post("/mfa/{user_id}/enable", response_class=None)
async def admin_mfa_enable(
    request: Request,
    user_id: int,
    verification_code: str = Form(...),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Abilita MFA per un utente privilegiato."""
    try:
        # Recupera l'utente
        target_user = db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        if not target_user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esegui prima il setup dell'MFA"
            )
        
        # Abilita MFA
        success = mfa_service.enable_mfa(target_user, target_user.mfa_secret, verification_code)
        
        if success:
            db.commit()
            return {"message": "MFA abilitato con successo"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Codice di verifica non valido"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'abilitazione MFA: {str(e)}"
        )

@router.post("/mfa/{user_id}/disable", response_class=None)
async def admin_mfa_disable(
    request: Request,
    user_id: int,
    verification_code: str = Form(...),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user=Depends(require_permission_in_tenant("manage_users")),
    db: Session = Depends(get_db)
):
    """Disabilita MFA per un utente privilegiato."""
    try:
        # Recupera l'utente
        target_user = db.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        if not target_user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA non abilitato"
            )
        
        # Disabilita MFA
        success = mfa_service.disable_mfa(target_user, verification_code)
        
        if success:
            db.commit()
            return {"message": "MFA disabilitato con successo"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Codice di verifica non valido"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la disabilitazione MFA: {str(e)}"
        ) 