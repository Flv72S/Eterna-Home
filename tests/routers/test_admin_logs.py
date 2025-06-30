import os
import uuid
import json
import pytest
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
    # Crea utente, ruolo, permesso e assegnazione
    user = User(username="logadmin", email="logadmin@example.com", hashed_password="x", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    role = Role(name="LogViewer", description="Can view logs")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    perm = Permission(name="view_logs", description="View logs")
    db_session.add(perm)
    db_session.commit()
    db_session.refresh(perm)
    
    role.permissions.append(perm)
    db_session.commit()
    
    tenant_id = uuid.uuid4()
    utr = UserTenantRole(user_id=user.id, tenant_id=tenant_id, role_id=role.id)
    db_session.add(utr)
    db_session.commit()
    
    token = create_access_token({"sub": user.email, "user_id": str(user.id), "tenant_id": str(tenant_id)})
    return user, token, tenant_id

@pytest.fixture
def test_user_without_view_logs(db_session):
    user = User(username="nolog", email="nolog@example.com", hashed_password="x", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    role = Role(name="NoLog", description="No log access")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    tenant_id = uuid.uuid4()
    utr = UserTenantRole(user_id=user.id, tenant_id=tenant_id, role_id=role.id)
    db_session.add(utr)
    db_session.commit()
    
    token = create_access_token({"sub": user.email, "user_id": str(user.id), "tenant_id": str(tenant_id)})
    return user, token, tenant_id

# Test 1 – Accesso Autorizzato
def test_accesso_autorizzato(test_user_with_view_logs, monkeypatch):
    user, token, tenant_id = test_user_with_view_logs
    # Mock log file
    log_data = {
        "timestamp": "2024-06-01T12:00:00Z",
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "event": "user_login",
        "status": "success",
        "message": "Login effettuato",
        "level": "INFO"
    }
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log_data])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    assert response.status_code == 200
    assert "Login effettuato" in response.text

# Test 2 – Accesso Negato
def test_accesso_negato(test_user_without_view_logs):
    user, token, tenant_id = test_user_without_view_logs
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    assert response.status_code == 403

# Test 3 – Filtri
def test_filtri_log(test_user_with_view_logs, monkeypatch):
    user, token, tenant_id = test_user_with_view_logs
    log1 = {
        "timestamp": "2024-06-01T12:00:00Z",
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "event": "user_login",
        "status": "success",
        "message": "Login effettuato",
        "level": "INFO"
    }
    log2 = {
        "timestamp": "2024-06-01T13:00:00Z",
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "event": "file_upload",
        "status": "success",
        "message": "File caricato",
        "level": "INFO"
    }
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log1, log2])
    headers = {"Authorization": f"Bearer {token}"}
    # Filtro per event_type
    response = client.get(f"/admin/logs/app?event_type=file_upload", headers=headers)
    assert response.status_code == 200
    assert "File caricato" in response.text
    assert "Login effettuato" not in response.text

# Test 4 – Sicurezza Tenant
def test_sicurezza_tenant(test_user_with_view_logs, monkeypatch):
    user, token, tenant_id = test_user_with_view_logs
    log1 = {
        "timestamp": "2024-06-01T12:00:00Z",
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "event": "user_login",
        "status": "success",
        "message": "Login effettuato",
        "level": "INFO"
    }
    log2 = {
        "timestamp": "2024-06-01T13:00:00Z",
        "tenant_id": str(uuid.uuid4()),  # Altro tenant
        "user_id": str(user.id),
        "event": "user_login",
        "status": "success",
        "message": "Login altro tenant",
        "level": "INFO"
    }
    monkeypatch.setattr("app.routers.admin.logs.read_log_file", lambda *a, **kw: [log1, log2])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/admin/logs/app", headers=headers)
    assert response.status_code == 200
    assert "Login effettuato" in response.text
    assert "Login altro tenant" not in response.text 