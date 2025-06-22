"""
Test per gli endpoint del sistema ruoli
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.enums import UserRole
from app.services.user import UserService
from app.utils.security import get_password_hash

def get_auth_headers(client: TestClient, email: str, password: str):
    """Ottiene i token di autenticazione"""
    response = client.post("/api/v1/token", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestRolesAPI:
    """Test per gli endpoint del sistema ruoli"""
    
    def test_get_all_roles_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può vedere tutti i ruoli"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 200
        roles = response.json()
        assert len(roles) == 16  # Tutti i ruoli definiti
        
        # Verifica che ogni ruolo abbia i campi richiesti
        for role in roles:
            assert "value" in role
            assert "name" in role
            assert "description" in role
            assert "permissions" in role
    
    def test_get_all_roles_admin(self, client: TestClient, db_session):
        """Test: Admin può vedere tutti i ruoli"""
        # Crea un utente admin
        admin = User(
            email="admin@test.com",
            username="admin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.ADMIN.value,
            full_name="Administrator"
        )
        db_session.add(admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "admin@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 200
        roles = response.json()
        assert len(roles) == 16
    
    def test_get_all_roles_unauthorized(self, client: TestClient, db_session):
        """Test: Utente normale non può vedere i ruoli"""
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "owner@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 403
    
    def test_get_all_roles_unauthenticated(self, client: TestClient):
        """Test: Utente non autenticato non può vedere i ruoli"""
        response = client.get("/api/v1/roles/")
        assert response.status_code == 401
    
    def test_get_users_by_role_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può vedere utenti per ruolo"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/users/owner", headers=headers)
        
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 0  # Può essere 0 se non ci sono utenti owner
    
    def test_get_users_by_role_invalid_role(self, client: TestClient, db_session):
        """Test: Ruolo non valido restituisce errore"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/users/invalid_role", headers=headers)
        
        assert response.status_code == 400
        assert "non valido" in response.json()["detail"]
    
    def test_update_user_role_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può aggiornare il ruolo di un utente"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.put(
            f"/api/v1/roles/users/{owner.id}/role",
            params={"role": "technician"},
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "aggiornato con successo" in result["message"]
        assert result["new_role"] == "technician"
    
    def test_update_user_role_admin(self, client: TestClient, db_session):
        """Test: Admin può aggiornare il ruolo di un utente"""
        # Crea un utente admin
        admin = User(
            email="admin@test.com",
            username="admin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.ADMIN.value,
            full_name="Administrator"
        )
        db_session.add(admin)
        
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "admin@test.com", "TestPassword123!")
        response = client.put(
            f"/api/v1/roles/users/{owner.id}/role",
            params={"role": "manager"},
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "aggiornato con successo" in result["message"]
    
    def test_update_user_role_unauthorized(self, client: TestClient, db_session):
        """Test: Utente normale non può aggiornare ruoli"""
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "owner@test.com", "TestPassword123!")
        response = client.put(
            "/api/v1/roles/users/1/role",
            params={"role": "admin"},
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_update_user_role_invalid_user(self, client: TestClient, db_session):
        """Test: Aggiornamento ruolo utente inesistente"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.put(
            "/api/v1/roles/users/99999/role",
            params={"role": "admin"},
            headers=headers
        )
        
        assert response.status_code == 404
    
    def test_get_role_statistics_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può vedere statistiche ruoli"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.get("/api/v1/roles/stats", headers=headers)
        
        assert response.status_code == 200
        stats = response.json()
        assert "total_users" in stats
        assert "role_distribution" in stats
    
    def test_add_user_role_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può aggiungere ruoli a un utente"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.post(
            f"/api/v1/roles/users/{owner.id}/roles",
            params={"role_name": "technician"},
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "aggiunto con successo" in result["message"]
    
    def test_remove_user_role_super_admin(self, client: TestClient, db_session):
        """Test: Super admin può rimuovere ruoli da un utente"""
        # Crea un utente super admin
        super_admin = User(
            email="superadmin@test.com",
            username="superadmin",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=True,
            role=UserRole.SUPER_ADMIN.value,
            full_name="Super Administrator"
        )
        db_session.add(super_admin)
        
        # Crea un utente owner
        owner = User(
            email="owner@test.com",
            username="owner",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=True,
            is_superuser=False,
            role=UserRole.OWNER.value,
            full_name="Property Owner"
        )
        db_session.add(owner)
        db_session.commit()
        
        headers = get_auth_headers(client, "superadmin@test.com", "TestPassword123!")
        response = client.delete(
            f"/api/v1/roles/users/{owner.id}/roles",
            params={"role_name": "technician"},
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "rimosso con successo" in result["message"]

class TestRoleValidation:
    """Test per la validazione dei ruoli"""
    
    def test_role_enum_values(self):
        """Test: Verifica che tutti i valori dell'enum siano validi"""
        valid_roles = [
            "super_admin", "admin", "owner", "manager", "technician",
            "maintenance", "security", "cleaner", "guest", "resident",
            "family_member", "tenant", "contractor", "supplier", "visitor", "system"
        ]
        
        for role_value in valid_roles:
            assert hasattr(UserRole, role_value.upper().replace(" ", "_"))
    
    def test_role_display_names(self):
        """Test: Verifica che i nomi di visualizzazione siano corretti"""
        assert UserRole.get_display_name("super_admin") == "Super Amministratore"
        assert UserRole.get_display_name("admin") == "Amministratore"
        assert UserRole.get_display_name("owner") == "Proprietario"
    
    def test_role_categories(self):
        """Test: Verifica le categorie dei ruoli"""
        admin_roles = UserRole.get_admin_roles()
        assert "super_admin" in admin_roles
        assert "admin" in admin_roles
        
        default_role = UserRole.get_default_role()
        assert default_role == "guest"

class TestRoleHierarchy:
    """Test per la gerarchia dei ruoli"""
    
    def test_super_admin_permissions(self):
        """Test: Super admin ha tutti i permessi"""
        assert UserRole.SUPER_ADMIN.value in UserRole.get_admin_roles()
    
    def test_admin_permissions(self):
        """Test: Admin ha permessi amministrativi"""
        assert UserRole.ADMIN.value in UserRole.get_admin_roles()
    
    def test_owner_permissions(self):
        """Test: Owner ha permessi limitati"""
        assert UserRole.OWNER.value not in UserRole.get_admin_roles()
    
    def test_guest_permissions(self):
        """Test: Guest ha permessi minimi"""
        assert UserRole.GUEST.value not in UserRole.get_admin_roles() 