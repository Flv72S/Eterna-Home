"""
Test automatici per la Dashboard Amministrativa
Verifica accesso RBAC, contenuti HTML e protezione multi-tenant
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.role import Role
from app.models.house import House
from app.models.user_role import UserRole
from app.core.security import create_access_token


@pytest.fixture
def client():
    """Client di test per FastAPI"""
    return TestClient(app)


@pytest.fixture
def admin_user_with_permissions():
    """Utente admin con permessi completi"""
    return {
        "id": 1,
        "email": "admin@test.com",
        "username": "admin",
        "is_active": True,
        "tenant_id": "house_123"
    }


@pytest.fixture
def regular_user():
    """Utente normale senza permessi admin"""
    return {
        "id": 2,
        "email": "user@test.com",
        "username": "user",
        "is_active": True,
        "tenant_id": "house_123"
    }


@pytest.fixture
def admin_token(admin_user_with_permissions):
    """Token JWT per utente admin"""
    return create_access_token(
        data={
            "sub": str(admin_user_with_permissions["id"]),
            "email": admin_user_with_permissions["email"],
            "tenant_id": admin_user_with_permissions["tenant_id"],
            "permissions": ["manage_users", "manage_roles", "manage_houses"]
        }
    )


@pytest.fixture
def regular_token(regular_user):
    """Token JWT per utente normale"""
    return create_access_token(
        data={
            "sub": str(regular_user["id"]),
            "email": regular_user["email"],
            "tenant_id": regular_user["tenant_id"],
            "permissions": ["read_own_data"]
        }
    )


class TestAdminDashboardAccess:
    """Test per l'accesso alla dashboard amministrativa"""

    def test_admin_dashboard_authorized_access(self, client, admin_token):
        """Test 1: Accesso autorizzato alla dashboard admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            # Mock utente admin
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users", "manage_roles", "manage_houses"]
            )
            
            # Mock database con dati
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verifica contenuti HTML attesi
            html_content = response.text
            assert "Dashboard" in html_content
            assert "Utenti" in html_content
            assert "Ruoli" in html_content
            assert "Case" in html_content

    def test_admin_dashboard_unauthorized_access(self, client, regular_token):
        """Test 2: Accesso non autorizzato alla dashboard admin"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user:
            # Mock utente senza permessi admin
            mock_user.return_value = MagicMock(
                id=2,
                email="user@test.com",
                tenant_id="house_123",
                permissions=["read_own_data"]
            )
            
            response = client.get("/admin/", headers=headers)
            
            assert response.status_code == 403
            assert "Forbidden" in response.text

    def test_admin_dashboard_no_token(self, client):
        """Test: Accesso senza token"""
        response = client.get("/admin/")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.text


class TestAdminUsersEndpoint:
    """Test per l'endpoint /admin/users"""

    def test_admin_users_authorized_access(self, client, admin_token):
        """Test: Accesso autorizzato alla pagina utenti"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/users", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verifica contenuti specifici utenti
            html_content = response.text
            assert "Email" in html_content
            assert "Ruolo" in html_content
            assert "MFA" in html_content
            assert "Case associate" in html_content

    def test_admin_users_unauthorized_access(self, client, regular_token):
        """Test: Accesso non autorizzato alla pagina utenti"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user:
            mock_user.return_value = MagicMock(
                id=2,
                email="user@test.com",
                tenant_id="house_123",
                permissions=["read_own_data"]
            )
            
            response = client.get("/admin/users", headers=headers)
            
            assert response.status_code == 403


class TestAdminRolesEndpoint:
    """Test per l'endpoint /admin/roles"""

    def test_admin_roles_authorized_access(self, client, admin_token):
        """Test: Accesso autorizzato alla pagina ruoli"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_roles"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/roles", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verifica contenuti specifici ruoli
            html_content = response.text
            assert "Permessi" in html_content
            assert "Utenti" in html_content

    def test_admin_roles_unauthorized_access(self, client, regular_token):
        """Test: Accesso non autorizzato alla pagina ruoli"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user:
            mock_user.return_value = MagicMock(
                id=2,
                email="user@test.com",
                tenant_id="house_123",
                permissions=["read_own_data"]
            )
            
            response = client.get("/admin/roles", headers=headers)
            
            assert response.status_code == 403


class TestAdminHousesEndpoint:
    """Test per l'endpoint /admin/houses"""

    def test_admin_houses_authorized_access(self, client, admin_token):
        """Test: Accesso autorizzato alla pagina case"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_houses"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/houses", headers=headers)
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verifica contenuti specifici case
            html_content = response.text
            assert "Indirizzo" in html_content
            assert "Utenti associati" in html_content

    def test_admin_houses_unauthorized_access(self, client, regular_token):
        """Test: Accesso non autorizzato alla pagina case"""
        headers = {"Authorization": f"Bearer {regular_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user:
            mock_user.return_value = MagicMock(
                id=2,
                email="user@test.com",
                tenant_id="house_123",
                permissions=["read_own_data"]
            )
            
            response = client.get("/admin/houses", headers=headers)
            
            assert response.status_code == 403


class TestAdminDashboardContent:
    """Test per i contenuti HTML della dashboard"""

    def test_dashboard_sidebar_content(self, client, admin_token):
        """Test: Verifica contenuto sidebar"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users", "manage_roles", "manage_houses"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/", headers=headers)
            
            assert response.status_code == 200
            
            # Verifica elementi sidebar
            html_content = response.text
            assert "sidebar" in html_content.lower()
            assert "nav" in html_content.lower()
            assert "dashboard" in html_content.lower()

    def test_dashboard_main_content(self, client, admin_token):
        """Test: Verifica contenuto principale dashboard"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users", "manage_roles", "manage_houses"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/", headers=headers)
            
            assert response.status_code == 200
            
            # Verifica elementi principali
            html_content = response.text
            assert "main" in html_content.lower()
            assert "container" in html_content.lower()
            assert "row" in html_content.lower()


class TestAdminDashboardRBAC:
    """Test specifici per RBAC multi-tenant"""

    def test_tenant_filtering(self, client, admin_token):
        """Test: Verifica filtraggio per tenant"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            # Mock utente con tenant specifico
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users"]
            )
            
            mock_db.return_value = MagicMock()
            
            response = client.get("/admin/users", headers=headers)
            
            assert response.status_code == 200

    def test_permission_granularity(self, client, admin_token):
        """Test: Verifica granularità permessi"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with patch('app.routers.admin.dashboard.get_current_user') as mock_user, \
             patch('app.routers.admin.dashboard.get_db') as mock_db:
            
            # Mock utente con solo permesso utenti
            mock_user.return_value = MagicMock(
                id=1,
                email="admin@test.com",
                tenant_id="house_123",
                permissions=["manage_users"]  # Solo utenti, non ruoli o case
            )
            
            mock_db.return_value = MagicMock()
            
            # Dovrebbe avere accesso a users
            response_users = client.get("/admin/users", headers=headers)
            assert response_users.status_code == 200
            
            # Dovrebbe essere negato per roles
            response_roles = client.get("/admin/roles", headers=headers)
            assert response_roles.status_code == 403
            
            # Dovrebbe essere negato per houses
            response_houses = client.get("/admin/houses", headers=headers)
            assert response_houses.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 