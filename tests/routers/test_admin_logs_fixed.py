import os
import uuid
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.user_tenant_role import UserTenantRole
from app.models.role import Role
from app.models.permission import Permission
from app.core.security import create_access_token

client = TestClient(app)

# Utility per setup utente e token
@pytest.fixture
def test_user_with_view_logs(db_session):
    unique = str(uuid.uuid4())[:8]
    user = User(
        username=f"logadmin_{unique}",
        email=f"logadmin_{unique}@example.com",
        hashed_password="x",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tenant_id=uuid.uuid4(),
        role="admin",  # Ruolo admin che ha il permesso view_logs
        mfa_enabled=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea ruolo admin (che ha il permesso view_logs)
    role = Role(name="admin", description="Administrator role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    # Crea permesso view_logs se non esiste
    existing_perm = db_session.query(Permission).filter(Permission.name == "view_logs").first()
    if not existing_perm:
        perm = Permission(name="view_logs", description="Can view system logs")
        db_session.add(perm)
        db_session.commit()
        db_session.refresh(perm)
    else:
        perm = existing_perm
    
    # Associa ruolo e permesso
    from app.models.role_permission import RolePermission
    role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(role_perm)
    db_session.commit()
    
    # Associa utente al tenant con il ruolo admin
    tenant_id = uuid.uuid4()
    utr = UserTenantRole(user_id=user.id, tenant_id=tenant_id, role_id=role.id, role=role.name)
    db_session.add(utr)
    db_session.commit()
    
    token = create_access_token({"sub": user.email, "user_id": str(user.id), "tenant_id": str(tenant_id)})
    return user, token, tenant_id

@pytest.fixture
def test_user_without_view_logs(db_session):
    unique = str(uuid.uuid4())[:8]
    user = User(
        username=f"nolog_{unique}",
        email=f"nolog_{unique}@example.com",
        hashed_password="x",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        tenant_id=uuid.uuid4(),
        role="guest",  # Ruolo guest che NON ha il permesso view_logs
        mfa_enabled=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea ruolo guest (che NON ha il permesso view_logs)
    role = Role(name="guest", description="Guest role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    # Associa utente al tenant con il ruolo guest
    tenant_id = uuid.uuid4()
    utr = UserTenantRole(user_id=user.id, tenant_id=tenant_id, role_id=role.id, role=role.name)
    db_session.add(utr)
    db_session.commit()
    
    token = create_access_token({"sub": user.email, "user_id": str(user.id), "tenant_id": str(tenant_id)})
    return user, token, tenant_id

def test_accesso_autorizzato(test_user_with_view_logs, monkeypatch):
    """Test accesso autorizzato ai log"""
    user, token, tenant_id = test_user_with_view_logs
    
    # Mock dei dati di log
    log_data = {
        "timestamp": "2024-01-01T10:00:00Z",
        "level": "INFO",
        "event": "user_login",
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),
        "message": "User logged in successfully"
    }
    
    # Mock della funzione read_log_file
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log_data])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    
    assert response.status_code == 200
    assert "logs" in response.json()

def test_accesso_negato(test_user_without_view_logs):
    """Test accesso negato ai log"""
    user, token, tenant_id = test_user_without_view_logs
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    
    assert response.status_code == 403

def test_filtri_log(test_user_with_view_logs, monkeypatch):
    """Test filtri sui log"""
    user, token, tenant_id = test_user_with_view_logs
    
    # Mock dei dati di log
    log1 = {
        "timestamp": "2024-01-01T10:00:00Z",
        "level": "INFO",
        "event": "file_upload",
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),
        "message": "File uploaded"
    }
    log2 = {
        "timestamp": "2024-01-01T11:00:00Z",
        "level": "INFO", 
        "event": "user_login",
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),
        "message": "User logged in"
    }
    
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log1, log2])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app?event_type=file_upload", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1
    assert data["logs"][0]["event"] == "file_upload"

def test_sicurezza_tenant(test_user_with_view_logs, monkeypatch):
    """Test sicurezza multi-tenant"""
    user, token, tenant_id = test_user_with_view_logs
    
    # Mock dei dati di log di un tenant diverso
    other_tenant_id = uuid.uuid4()
    log1 = {
        "timestamp": "2024-01-01T10:00:00Z",
        "level": "INFO",
        "event": "file_upload",
        "user_id": str(user.id),
        "tenant_id": str(tenant_id),  # Tenant corretto
        "message": "File uploaded"
    }
    log2 = {
        "timestamp": "2024-01-01T11:00:00Z",
        "level": "INFO",
        "event": "file_upload", 
        "user_id": str(user.id),
        "tenant_id": str(other_tenant_id),  # Tenant diverso
        "message": "File uploaded to other tenant"
    }
    
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log1, log2])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    # Dovrebbe vedere solo i log del proprio tenant
    assert len(data["logs"]) == 1
    assert data["logs"][0]["tenant_id"] == str(tenant_id) 