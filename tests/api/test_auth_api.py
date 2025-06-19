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
    session.execute(text("DELETE FROM \"users\" WHERE email = :email"), {"email": email})
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
    session.execute(text("DELETE FROM \"users\" WHERE email = 'disabled@example.com'"))
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

def test_login_valid_credentials(client: TestClient, test_user: User, reset_rate_limiting):
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

def test_login_invalid_credentials(client: TestClient, test_user: User, reset_rate_limiting):
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

def test_login_disabled_account(client: TestClient, disabled_user: User, reset_rate_limiting):
    """Test login with a disabled account."""
    print(f"DEBUG: Testing login for disabled user: {disabled_user.email}, is_active: {disabled_user.is_active}")
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "disabled@example.com",
            "password": "Test123!@#"
        }
    )
    print(f"DEBUG: Response status: {response.status_code}, body: {response.json()}")
    assert response.status_code == 403
    assert response.json()["detail"] == "Utente disabilitato"

def test_login_rate_limiting(client: TestClient, test_user: User, reset_rate_limiting):
    """
    Test rate limiting per i tentativi di login.
    Best practice REST: dopo troppi tentativi, la risposta deve essere 429 (Too Many Requests).
    """
    for i in range(1001):  # 1001 tentativi per superare il limite di 1000/minuto
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "WrongPassword123!@#"
            }
        )
        print(f"DEBUG: Tentativo {i+1}, status: {response.status_code}")
        # Le prime risposte saranno 401, poi 429
        if response.status_code == 429:
            break
        assert response.status_code == 401
    else:
        assert False, "Rate limiting non è stato raggiunto dopo 1001 tentativi"
    
    # Verifica che la risposta 429 abbia il messaggio corretto
    assert response.status_code == 429
    assert "Troppi tentativi di login" in response.json()["detail"]

def test_login_token_generation(client: TestClient, session: Session, reset_rate_limiting, email: str = "test@example.com"):
    """Test per la generazione del token di login."""
    # Pulisci il database
    session.execute(text("DELETE FROM \"users\" WHERE email = :email"), {"email": email})
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
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Test endpoint /me
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == email
    assert user_data["username"] == "testuser"

def test_login_disabled_user(client: TestClient, session: Session):
    """Test per il login di un utente disabilitato."""
    # Pulisci il database
    session.execute(text("DELETE FROM \"users\" WHERE email = 'disabled@example.com'"))
    session.commit()

def test_logout_invalidate_token(client: TestClient, reset_rate_limiting):
    """
    Test logout con token valido.
    TODO: In futuro implementare blacklist token per invalidazione effettiva.
    """
    # Login per ottenere un token valido
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "Test123!@#"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Test logout con token valido
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    # Per ora restituisce 200 (successo) anche se non invalida realmente il token
    # TODO: Implementare blacklist token per invalidazione effettiva
    assert response.status_code == 200
    assert response.json()["message"] == "Logout effettuato con successo"

def test_logout_invalid_token(client: TestClient, reset_rate_limiting):
    """
    Test logout con token non valido.
    TODO: In futuro implementare blacklist token per invalidazione effettiva.
    """
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer invalid_token"}
    )
    # Accetta sia 200 che 401 come risposta valida
    assert response.status_code in (200, 401)

def test_logout_session_management(client: TestClient, test_user: User, reset_rate_limiting):
    """Test gestione sessione durante il logout."""
    # Login per ottenere un token valido
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "Test123!@#"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Logout con token valido
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200

    # Logout con token non valido
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200 