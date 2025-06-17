"""Test authentication endpoints."""
import pytest
import time
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session
from app.core.config import settings
from app.utils.security import create_access_token
from app.utils.password import get_password_hash

@pytest.fixture(name="client")
def client_fixture(test_db_session: Session):
    def get_session_override():
        return test_db_session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
def test_user_fixture(test_db_session: Session):
    """Crea un utente di test."""
    print("\n[DEBUG] Creating test user...")
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
        full_name="Test User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    print("[DEBUG] Test user created successfully")
    return user

def test_jwt_token_structure(client: TestClient, test_user: User):
    """Test che il token JWT abbia la struttura corretta."""
    print("\n[DEBUG] Starting JWT token structure test...")
    response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "testpassword"}
    )
    print("[DEBUG] Token request completed")
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Decodifica il token
    token = token_data["access_token"]
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert "sub" in payload
    assert "exp" in payload
    assert payload["sub"] == test_user.email

    # Verifica che il token sia valido per 30 minuti
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    assert exp_time > now
    assert exp_time - now <= timedelta(minutes=30)
    print("[DEBUG] JWT token structure test completed successfully")

def test_login_invalid_credentials(client: TestClient):
    """Test il login con credenziali non valide."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_inactive_user(client: TestClient, test_db_session: Session):
    """Test il login con un utente disattivato."""
    # Crea un utente inattivo
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=False,
        is_superuser=False,
        full_name="Inactive User"
    )
    test_db_session.add(inactive_user)
    test_db_session.commit()

    response = client.post(
        "/api/v1/auth/token",
        data={"username": inactive_user.email, "password": "testpassword"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Utente disabilitato"

def test_refresh_token(client: TestClient, test_user: User):
    """Test il refresh del token."""
    # Prima ottieni un token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Poi prova a fare il refresh
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    new_token_data = response.json()
    assert "access_token" in new_token_data
    assert new_token_data["token_type"] == "bearer"
    assert new_token_data["access_token"] != token  # Il token dovrebbe essere diverso

def test_refresh_token_invalid(client: TestClient):
    """Test il refresh con un token non valido."""
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_logout(client: TestClient, test_user: User):
    """Test il logout."""
    # Prima ottieni un token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Poi prova a fare il logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"

def test_get_current_user(client: TestClient, test_user: User):
    """Test l'endpoint /me."""
    # Prima ottieni un token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Poi prova a ottenere i dati dell'utente
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert "hashed_password" not in data