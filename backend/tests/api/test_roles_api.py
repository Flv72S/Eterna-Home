import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app')))
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.core.security import create_access_token
from app.utils.password import get_password_hash

client = TestClient(app)


@pytest.fixture
def superuser(db_session: Session):
    """Crea un utente superuser per i test"""
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=True,
        username="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session):
    """Crea un utente normale per i test"""
    user = User(
        email="user@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
        username="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_role(db_session: Session):
    """Crea un ruolo di test"""
    role = Role(
        name="test_role",
        description="Ruolo di test",
        permissions=["read:houses", "write:houses"]
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


def get_auth_headers(user: User):
    """Genera headers di autenticazione per un utente"""
    access_token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {access_token}"}


class TestRolesAPI:
    """Test per gli endpoint CRUD dei ruoli"""

    def test_get_roles_superuser_success(self, db_session: Session, superuser: User, test_role: Role):
        """Test 4.1.2.1: GET /roles/ - lista ruoli (superuser)"""
        headers = get_auth_headers(superuser)
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 200
        roles = response.json()
        assert isinstance(roles, list)
        assert len(roles) >= 1
        
        # Verifica che il ruolo di test sia presente
        role_names = [role["name"] for role in roles]
        assert "test_role" in role_names

    def test_get_roles_regular_user_forbidden(self, db_session: Session, regular_user: User):
        """Test: GET /roles/ - accesso negato per utente normale"""
        headers = get_auth_headers(regular_user)
        response = client.get("/api/v1/roles/", headers=headers)
        
        assert response.status_code == 403
        assert "Solo i superuser possono visualizzare i ruoli" in response.json()["detail"]

    def test_get_roles_unauthenticated(self):
        """Test: GET /roles/ - accesso negato senza autenticazione"""
        response = client.get("/api/v1/roles/")
        
        assert response.status_code == 401

    def test_create_role_superuser_success(self, db_session: Session, superuser: User):
        """Test 4.1.2.2: POST /roles/ - crea ruolo (superuser)"""
        headers = get_auth_headers(superuser)
        role_data = {
            "name": "new_role",
            "description": "Nuovo ruolo di test",
            "permissions": ["read:users", "write:users"]
        }
        
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        
        assert response.status_code == 201
        role = response.json()
        assert role["name"] == "new_role"
        assert role["description"] == "Nuovo ruolo di test"
        assert role["permissions"] == ["read:users", "write:users"]
        assert "id" in role

    def test_create_role_duplicate_name(self, db_session: Session, superuser: User, test_role: Role):
        """Test: POST /roles/ - errore per nome duplicato"""
        headers = get_auth_headers(superuser)
        role_data = {
            "name": "test_role",  # Nome già esistente
            "description": "Ruolo duplicato",
            "permissions": ["read:houses"]
        }
        
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        
        assert response.status_code == 400
        assert "già esistente" in response.json()["detail"]

    def test_create_role_regular_user_forbidden(self, db_session: Session, regular_user: User):
        """Test: POST /roles/ - accesso negato per utente normale"""
        headers = get_auth_headers(regular_user)
        role_data = {
            "name": "new_role",
            "description": "Nuovo ruolo",
            "permissions": ["read:users"]
        }
        
        response = client.post("/api/v1/roles/", json=role_data, headers=headers)
        
        assert response.status_code == 403
        assert "Solo i superuser possono creare ruoli" in response.json()["detail"]

    def test_get_role_superuser_success(self, db_session: Session, superuser: User, test_role: Role):
        """Test 4.1.2.3: GET /roles/{id} - dettagli ruolo (superuser)"""
        headers = get_auth_headers(superuser)
        response = client.get(f"/api/v1/roles/{test_role.id}", headers=headers)
        
        assert response.status_code == 200
        role = response.json()
        assert role["id"] == test_role.id
        assert role["name"] == "test_role"
        assert role["description"] == "Ruolo di test"

    def test_get_role_not_found(self, db_session: Session, superuser: User):
        """Test: GET /roles/{id} - ruolo non trovato"""
        headers = get_auth_headers(superuser)
        response = client.get("/api/v1/roles/999", headers=headers)
        
        assert response.status_code == 404
        assert "Ruolo non trovato" in response.json()["detail"]

    def test_get_role_regular_user_forbidden(self, db_session: Session, regular_user: User, test_role: Role):
        """Test: GET /roles/{id} - accesso negato per utente normale"""
        headers = get_auth_headers(regular_user)
        response = client.get(f"/api/v1/roles/{test_role.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Solo i superuser possono visualizzare i dettagli dei ruoli" in response.json()["detail"]

    def test_update_role_superuser_success(self, db_session: Session, superuser: User, test_role: Role):
        """Test 4.1.2.3: PUT /roles/{id} - modifica ruolo (superuser)"""
        headers = get_auth_headers(superuser)
        update_data = {
            "name": "updated_role",
            "description": "Ruolo aggiornato",
            "permissions": ["read:houses", "write:houses", "delete:houses"]
        }
        
        response = client.put(f"/api/v1/roles/{test_role.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        role = response.json()
        assert role["name"] == "updated_role"
        assert role["description"] == "Ruolo aggiornato"
        assert len(role["permissions"]) == 3

    def test_update_role_partial(self, db_session: Session, superuser: User, test_role: Role):
        """Test: PUT /roles/{id} - aggiornamento parziale"""
        headers = get_auth_headers(superuser)
        update_data = {
            "description": "Solo descrizione aggiornata"
        }
        
        response = client.put(f"/api/v1/roles/{test_role.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        role = response.json()
        assert role["name"] == "test_role"  # Non cambiato
        assert role["description"] == "Solo descrizione aggiornata"

    def test_update_role_duplicate_name(self, db_session: Session, superuser: User, test_role: Role):
        """Test: PUT /roles/{id} - errore per nome duplicato"""
        # Crea un secondo ruolo
        second_role = Role(
            name="second_role",
            description="Secondo ruolo",
            permissions=["read:users"]
        )
        db_session.add(second_role)
        db_session.commit()
        
        headers = get_auth_headers(superuser)
        update_data = {
            "name": "second_role"  # Nome del secondo ruolo
        }
        
        response = client.put(f"/api/v1/roles/{test_role.id}", json=update_data, headers=headers)
        
        assert response.status_code == 400
        assert "già esistente" in response.json()["detail"]

    def test_update_role_regular_user_forbidden(self, db_session: Session, regular_user: User, test_role: Role):
        """Test: PUT /roles/{id} - accesso negato per utente normale"""
        headers = get_auth_headers(regular_user)
        update_data = {
            "description": "Aggiornamento non autorizzato"
        }
        
        response = client.put(f"/api/v1/roles/{test_role.id}", json=update_data, headers=headers)
        
        assert response.status_code == 403
        assert "Solo i superuser possono modificare i ruoli" in response.json()["detail"]

    def test_delete_role_superuser_success(self, db_session: Session, superuser: User):
        """Test 4.1.2.4: DELETE /roles/{id} - rimuove ruolo (superuser)"""
        # Crea un ruolo da eliminare
        role_to_delete = Role(
            name="role_to_delete",
            description="Ruolo da eliminare",
            permissions=["read:users"]
        )
        db_session.add(role_to_delete)
        db_session.commit()
        db_session.refresh(role_to_delete)
        
        headers = get_auth_headers(superuser)
        response = client.delete(f"/api/v1/roles/{role_to_delete.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verifica che il ruolo sia stato eliminato
        deleted_role = db_session.get(Role, role_to_delete.id)
        assert deleted_role is None

    def test_delete_role_with_users(self, db_session: Session, superuser: User, test_role: Role, regular_user: User):
        """Test: DELETE /roles/{id} - errore se ruolo assegnato a utenti"""
        # Assegna il ruolo all'utente
        user_role = UserRole(
            user_id=regular_user.id,
            role_id=test_role.id,
            assigned_by=superuser.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        headers = get_auth_headers(superuser)
        response = client.delete(f"/api/v1/roles/{test_role.id}", headers=headers)
        
        assert response.status_code == 400
        assert "ancora assegnato ad alcuni utenti" in response.json()["detail"]

    def test_delete_role_regular_user_forbidden(self, db_session: Session, regular_user: User, test_role: Role):
        """Test: DELETE /roles/{id} - accesso negato per utente normale"""
        headers = get_auth_headers(regular_user)
        response = client.delete(f"/api/v1/roles/{test_role.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Solo i superuser possono eliminare i ruoli" in response.json()["detail"]

    def test_delete_role_not_found(self, db_session: Session, superuser: User):
        """Test: DELETE /roles/{id} - ruolo non trovato"""
        headers = get_auth_headers(superuser)
        response = client.delete("/api/v1/roles/999", headers=headers)
        
        assert response.status_code == 404
        assert "Ruolo non trovato" in response.json()["detail"] 