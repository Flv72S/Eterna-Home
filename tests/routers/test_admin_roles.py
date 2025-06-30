"""
Test per il router admin roles e permessi.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission, RolePermission
from app.models.user_tenant_role import UserTenantRole
from app.models.house import House
import uuid

client = TestClient(app)

@pytest.fixture
def admin_user():
    """Crea un utente admin per i test."""
    return User(
        id=1,
        email="admin@test.com",
        username="admin",
        hashed_password="hashed_password",
        tenant_id=uuid.uuid4(),
        role="admin"
    )

@pytest.fixture
def test_tenant_id():
    """ID del tenant di test."""
    return uuid.uuid4()

@pytest.fixture
def admin_token(admin_user, test_tenant_id):
    """Token di accesso per admin."""
    return create_access_token(data={
        "sub": admin_user.email,
        "tenant_id": str(test_tenant_id),
        "roles": ["admin"]
    })

@pytest.fixture
def regular_user():
    """Crea un utente normale per i test."""
    return User(
        id=2,
        email="user@test.com",
        username="user",
        hashed_password="hashed_password",
        tenant_id=uuid.uuid4(),
        role="user"
    )

@pytest.fixture
def regular_token(regular_user, test_tenant_id):
    """Token di accesso per utente normale."""
    return create_access_token(data={
        "sub": regular_user.email,
        "tenant_id": str(test_tenant_id),
        "roles": ["user"]
    })

class TestAdminRolesAccess:
    """Test per l'accesso alle pagine dei ruoli."""

    def test_admin_roles_authorized_access(self, admin_token, test_tenant_id):
        """Test: Accesso autorizzato alla pagina ruoli."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/roles", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verifica contenuti specifici ruoli
            html_content = response.text
            assert "Gestione Ruoli e Permessi" in html_content
            assert "Nuovo Ruolo" in html_content

    def test_admin_roles_unauthorized_access(self, regular_token, test_tenant_id):
        """Test: Accesso non autorizzato alla pagina ruoli."""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=2,
                email="user@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["read_own_data"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            response = client.get("/admin/roles", headers=headers)
            
            assert response.status_code == 403

    def test_admin_roles_new_form_access(self, admin_token, test_tenant_id):
        """Test: Accesso al form di creazione ruolo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/roles/new", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            html_content = response.text
            assert "Nuovo Ruolo" in html_content
            assert "Permessi" in html_content

class TestRoleCRUD:
    """Test per le operazioni CRUD sui ruoli."""

    def test_create_role_success(self, admin_token, test_tenant_id):
        """Test: Creazione ruolo con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock per la verifica ruolo esistente
            mock_session.exec.return_value.first.return_value = None
            
            # Mock per il nuovo ruolo
            new_role = Role(id=1, name="editor", description="Editor role", tenant_id=test_tenant_id)
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            
            # Mock per i permessi
            mock_permission = Permission(id=1, name="read_documents", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = mock_permission
            
            response = client.post(
                "/admin/roles/new",
                headers=headers,
                data={
                    "name": "editor",
                    "description": "Editor role",
                    "permissions": ["read_documents"]
                }
            )
            
            assert response.status_code == 303  # Redirect
            assert response.headers["location"] == "/admin/roles"

    def test_create_role_duplicate_name(self, admin_token, test_tenant_id):
        """Test: Creazione ruolo con nome duplicato."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database - ruolo già esistente
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            existing_role = Role(id=1, name="editor", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = existing_role
            
            response = client.post(
                "/admin/roles/new",
                headers=headers,
                data={
                    "name": "editor",
                    "description": "Editor role",
                    "permissions": []
                }
            )
            
            assert response.status_code == 400

    def test_edit_role_form_access(self, admin_token, test_tenant_id):
        """Test: Accesso al form di modifica ruolo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock del ruolo esistente
            existing_role = Role(id=1, name="editor", description="Editor role", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = existing_role
            
            # Mock dei permessi del ruolo
            mock_permission = MagicMock()
            mock_permission.name = "read_documents"
            mock_session.exec.return_value.all.return_value = [mock_permission]
            
            response = client.get("/admin/roles/1/edit", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            html_content = response.text
            assert "Modifica Ruolo" in html_content
            assert "editor" in html_content

    def test_update_role_success(self, admin_token, test_tenant_id):
        """Test: Aggiornamento ruolo con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock del ruolo esistente
            existing_role = Role(id=1, name="editor", description="Editor role", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = existing_role
            
            # Mock per la verifica nome duplicato
            mock_session.exec.return_value.first.return_value = None
            
            # Mock per i permessi
            mock_permission = Permission(id=1, name="write_documents", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = mock_permission
            
            response = client.post(
                "/admin/roles/1/edit",
                headers=headers,
                data={
                    "name": "senior_editor",
                    "description": "Senior Editor role",
                    "permissions": ["write_documents"]
                }
            )
            
            assert response.status_code == 303  # Redirect
            assert response.headers["location"] == "/admin/roles"

    def test_delete_role_success(self, admin_token, test_tenant_id):
        """Test: Eliminazione ruolo con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock del ruolo esistente
            existing_role = Role(id=1, name="temp_role", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = existing_role
            
            # Mock per la verifica utenti associati (nessun utente)
            mock_session.exec.return_value.first.return_value = 0
            
            response = client.post("/admin/roles/1/delete", headers=headers)
            
            assert response.status_code == 303  # Redirect
            assert response.headers["location"] == "/admin/roles"

    def test_delete_role_with_users(self, admin_token, test_tenant_id):
        """Test: Eliminazione ruolo con utenti associati."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock del ruolo esistente
            existing_role = Role(id=1, name="admin", tenant_id=test_tenant_id)
            mock_session.exec.return_value.first.return_value = existing_role
            
            # Mock per la verifica utenti associati (1 utente)
            mock_session.exec.return_value.first.return_value = 1
            
            response = client.post("/admin/roles/1/delete", headers=headers)
            
            assert response.status_code == 400

class TestRoleAssignment:
    """Test per l'assegnazione di ruoli agli utenti."""

    def test_role_assign_form_access(self, admin_token, test_tenant_id):
        """Test: Accesso al form di assegnazione ruoli."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock degli utenti
            mock_user1 = MagicMock()
            mock_user1.id = 1
            mock_user1.username = "user1"
            mock_user1.email = "user1@test.com"
            
            mock_user2 = MagicMock()
            mock_user2.id = 2
            mock_user2.username = "user2"
            mock_user2.email = "user2@test.com"
            
            mock_session.exec.return_value.all.return_value = [mock_user1, mock_user2]
            
            # Mock dei ruoli
            mock_role1 = MagicMock()
            mock_role1.id = 1
            mock_role1.name = "editor"
            mock_role1.description = "Editor role"
            
            mock_role2 = MagicMock()
            mock_role2.id = 2
            mock_role2.name = "viewer"
            mock_role2.description = "Viewer role"
            
            mock_session.exec.return_value.all.return_value = [mock_role1, mock_role2]
            
            # Mock delle case
            mock_house1 = MagicMock()
            mock_house1.id = 1
            mock_house1.name = "Casa 1"
            mock_house1.address = "Via Roma 1"
            
            mock_session.exec.return_value.all.return_value = [mock_house1]
            
            response = client.get("/admin/roles/assign", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            html_content = response.text
            assert "Assegnazione Ruoli agli Utenti" in html_content
            assert "user1" in html_content
            assert "editor" in html_content

    def test_role_assign_success(self, admin_token, test_tenant_id):
        """Test: Assegnazione ruolo con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant, \
             patch('app.routers.admin.roles.UserTenantRole.add_user_to_tenant') as mock_add_user:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock dell'utente
            mock_user_obj = MagicMock()
            mock_user_obj.id = 2
            mock_session.exec.return_value.first.return_value = mock_user_obj
            
            # Mock del ruolo
            mock_role = MagicMock()
            mock_role.id = 1
            mock_role.name = "editor"
            mock_role.tenant_id = test_tenant_id
            mock_session.exec.return_value.first.return_value = mock_role
            
            # Mock della casa
            mock_house = MagicMock()
            mock_house.id = 1
            mock_house.tenant_id = test_tenant_id
            mock_session.exec.return_value.first.return_value = mock_house
            
            # Mock per la verifica associazione casa esistente
            mock_session.exec.return_value.first.return_value = None
            
            mock_add_user.return_value = MagicMock()
            
            response = client.post(
                "/admin/roles/assign",
                headers=headers,
                data={
                    "user_id": "2",
                    "role_id": "1",
                    "house_id": "1"
                }
            )
            
            assert response.status_code == 303  # Redirect
            assert response.headers["location"] == "/admin/roles"

class TestMFAManagement:
    """Test per la gestione MFA."""

    def test_mfa_management_access(self, admin_token, test_tenant_id):
        """Test: Accesso alla gestione MFA."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock degli utenti privilegiati
            mock_privileged_user = MagicMock()
            mock_privileged_user.id = 1
            mock_privileged_user.username = "admin"
            mock_privileged_user.email = "admin@test.com"
            mock_privileged_user.mfa_enabled = False
            mock_privileged_user.role = "admin"
            
            mock_session.exec.return_value.all.return_value = [mock_privileged_user]
            
            response = client.get("/admin/mfa", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            html_content = response.text
            assert "Gestione MFA" in html_content
            assert "admin@test.com" in html_content

    def test_mfa_setup_success(self, admin_token, test_tenant_id):
        """Test: Setup MFA con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant, \
             patch('app.routers.admin.roles.mfa_service.setup_mfa') as mock_setup:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock dell'utente target
            mock_target_user = MagicMock()
            mock_target_user.id = 2
            mock_session.exec.return_value.first.return_value = mock_target_user
            
            # Mock per la verifica ruolo privilegiato
            mock_tenant_role = MagicMock()
            mock_tenant_role.user_id = 2
            mock_tenant_role.tenant_id = test_tenant_id
            mock_tenant_role.role = "admin"
            mock_session.exec.return_value.first.return_value = mock_tenant_role
            
            # Mock del setup MFA
            mock_setup.return_value = {
                "secret": "test_secret",
                "qr_code": "test_qr_code",
                "backup_codes": ["backup1", "backup2"]
            }
            
            response = client.post("/admin/mfa/2/setup", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "secret" in data
            assert "qr_code" in data
            assert "backup_codes" in data

    def test_mfa_enable_success(self, admin_token, test_tenant_id):
        """Test: Abilitazione MFA con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant, \
             patch('app.routers.admin.roles.mfa_service.enable_mfa') as mock_enable:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock dell'utente target
            mock_target_user = MagicMock()
            mock_target_user.id = 2
            mock_target_user.mfa_secret = "test_secret"
            mock_session.exec.return_value.first.return_value = mock_target_user
            
            # Mock dell'abilitazione MFA
            mock_enable.return_value = True
            
            response = client.post(
                "/admin/mfa/2/enable",
                headers=headers,
                data={"verification_code": "123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "successo" in data["message"]

    def test_mfa_disable_success(self, admin_token, test_tenant_id):
        """Test: Disabilitazione MFA con successo."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.roles.get_current_user') as mock_user, \
             patch('app.routers.admin.roles.get_db') as mock_db, \
             patch('app.routers.admin.roles.get_current_tenant') as mock_tenant, \
             patch('app.routers.admin.roles.mfa_service.disable_mfa') as mock_disable:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id=str(test_tenant_id),
                permissions=["manage_users"]
            )
            
            mock_tenant.return_value = test_tenant_id
            
            # Mock del database
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Mock dell'utente target
            mock_target_user = MagicMock()
            mock_target_user.id = 2
            mock_target_user.mfa_enabled = True
            mock_session.exec.return_value.first.return_value = mock_target_user
            
            # Mock della disabilitazione MFA
            mock_disable.return_value = True
            
            response = client.post(
                "/admin/mfa/2/disable",
                headers=headers,
                data={"verification_code": "123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "disabilitato" in data["message"] 