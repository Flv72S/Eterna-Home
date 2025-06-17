import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, text
import time
import logging
from faker import Faker

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.core.security import get_password_hash

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

fake = Faker()

def create_user(session: Session, email: str, username: str, password: str, full_name: str) -> User:
    """Helper function to create a test user."""
    # Elimina eventuali utenti con la stessa email
    session.execute(text("DELETE FROM \"user\" WHERE email = :email"), {"email": email})
    session.commit()
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
        is_verified=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def test_user(session: Session) -> User:
    """Fixture per creare un utente di test."""
    user = create_user(
        session,
        email="test@example.com",
        username="testuser",
        password="Test123!@#",
        full_name="Test User"
    )
    return user

@pytest.fixture(name="disabled_user")
def disabled_user_fixture(session: Session):
    """Fixture per creare un utente disabilitato."""
    session.execute(text("DELETE FROM \"user\" WHERE email = 'disabled@example.com'"))
    session.commit()
    user = User(
        email="disabled@example.com",
        username="disableduser",
        hashed_password=get_password_hash("Test123!@#"),
        full_name="Disabled User",
        is_active=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def test_login_valid_credentials(client: TestClient, test_user: User):
    """Test login con credenziali valide."""
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient):
    """Test login with invalid credentials."""
    # Test with non-existent email
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword123"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenziali non valide"

    # Test with wrong password
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "wrongpassword123"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenziali non valide"

def test_login_disabled_account(client: TestClient, disabled_user: User):
    """Test login with a disabled account."""
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "disabled@example.com",
            "password": "Test123!@#"
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Utente disabilitato"

def test_login_rate_limiting(client: TestClient, test_user: User):
    """Test rate limiting per i tentativi di login."""
    # Simula 5 tentativi di login falliti in rapida successione
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "WrongPassword123!@#"
            }
        )
        assert response.status_code == 401

    # Il sesto tentativo dovrebbe essere bloccato dal rate limiting
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 429
    assert "Troppi tentativi di login" in response.json()["detail"]

    # Attendi il reset del rate limit
    time.sleep(60)  # Assumendo un rate limit di 5 tentativi per minuto

    # Verifica che il login funzioni dopo il reset
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    assert response.status_code == 200

def test_login_token_generation(client: TestClient, session: Session, email: str = "test@example.com"):
    """Test per la generazione del token di login."""
    # Pulisci il database
    session.execute(text("DELETE FROM \"user\" WHERE email = :email"), {"email": email})
    session.commit()

    # Crea un utente di test
    user_data = {
        "email": email,
        "username": "testuser",
        "password": "Test123!@#",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200

    # Test login
    login_data = {
        "username": email,
        "password": "Test123!@#"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test endpoint /me
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == email
    assert user_data["username"] == "testuser"

def test_login_disabled_user(client: TestClient, session: Session):
    """Test per il login di un utente disabilitato."""
    # Pulisci il database
    session.execute(text("DELETE FROM \"user\" WHERE email = 'disabled@example.com'"))
    session.commit()

def test_logout_invalidate_token(client: TestClient, test_user: User):
    """Test invalidazione del token durante il logout."""
    # Login per ottenere il token
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    token = response.json()["access_token"]

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verifica che il token non sia più valido
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_logout_invalid_token(client: TestClient):
    """Test logout con token non valido."""
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_logout_session_management(client: TestClient, test_user: User):
    """Test gestione della sessione durante il logout."""
    # Login per ottenere il token
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    token = response.json()["access_token"]

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verifica che non si possa fare logout due volte con lo stesso token
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401 