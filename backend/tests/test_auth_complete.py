import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text
import time

from app.main import app
from app.models.user import User
from app.db.session import get_session
from app.utils.password import get_password_hash
from app.core.config import settings

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
}

TEST_USER_DUPLICATE = {
    "email": "test@example.com",  # Email duplicata
    "password": "Test123!@#",
    "full_name": "Test User 2"
}

TEST_USER_INVALID_EMAIL = {
    "email": "invalid-email",
    "password": "Test123!@#",
    "full_name": "Test User 3"
}

TEST_USER_WEAK_PASSWORD = {
    "email": "weak@example.com",
    "password": "weak",
    "full_name": "Weak User"
}

TEST_USER_MISSING_FIELDS = {
    "email": "test3@example.com"
    # Password e full_name mancanti
}

@pytest.fixture
def client():
    return TestClient(app)

def test_user_creation_validation(client: TestClient):
    """Test validazione dati utente."""
    # Test dati mancanti
    response = client.post(f"{settings.API_V1_STR}/users/", json={"email": "test@example.com"})
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data)

def test_user_creation_duplicate(client: TestClient):
    """Test gestione utenti duplicati."""
    # Prima registrazione
    response = client.post(f"{settings.API_V1_STR}/users/", json=TEST_USER)
    assert response.status_code == 201
    
    # Seconda registrazione con stessa email
    response = client.post(f"{settings.API_V1_STR}/users/", json=TEST_USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email già registrata"

def test_user_profile(client: TestClient):
    """Test profilo utente."""
    # Registra utente
    response = client.post(f"{settings.API_V1_STR}/users/", json=TEST_USER)
    assert response.status_code == 201
    
    # Login per ottenere token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Recupera profilo
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]

def test_login_scenarios(client: TestClient):
    """Test vari scenari di login."""
    # Registra utente
    client.post(f"{settings.API_V1_STR}/users/", json=TEST_USER)

    # Test credenziali valide
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Test credenziali non valide
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": TEST_USER["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_rate_limiting(client: TestClient):
    """Test rate limiting on login attempts."""
    # Create user
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "rate@example.com",
            "password": "Test123!@#",
            "full_name": "Rate Test User"
        }
    )
    
    # Make multiple failed login attempts
    for _ in range(6):
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": "rate@example.com",
                "password": "wrongpassword"
            }
        )
    
    # The last attempt should be rate limited
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]

def test_create_user_success(client: TestClient):
    """Test successful user creation."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "test@example.com",
            "username": "test",
            "password": "Test123!@#",
            "full_name": "Test User"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data

def test_create_user_duplicate_email(client: TestClient):
    """Test user creation with duplicate email."""
    # First user
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "duplicate@example.com",
            "password": "Test123!@#",
            "full_name": "Test User 1"
        }
    )
    # Second user with same email
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "duplicate@example.com",
            "password": "Test123!@#",
            "full_name": "Test User 2"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email già registrata"

def test_create_user_invalid_email(client: TestClient):
    """Test user creation with invalid email."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "invalid-email",
            "password": "Test123!@#",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "email" in str(data)

def test_create_user_weak_password(client: TestClient):
    """Test user creation with weak password."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak User"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data)

def test_create_user_missing_fields(client: TestClient):
    """Test user creation with missing required fields."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": "test3@example.com"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data)

def test_get_current_user_success(client: TestClient):
    """Test recupero profilo utente con autenticazione valida."""
    # Crea utente
    client.post(f"{settings.API_V1_STR}/users/", json=TEST_USER)

    # Login per ottenere token
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Recupera profilo
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]

def test_get_current_user_no_auth(client: TestClient):
    """Test recupero profilo utente senza autenticazione."""
    response = client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user info with invalid token."""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_login_success(client: TestClient):
    """Test successful login."""
    # Create user first
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "login@example.com",
            "password": "Test123!@#",
            "full_name": "Login Test User"
        }
    )
    # Try to login
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "login@example.com",
            "password": "Test123!@#"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient):
    """Test login with invalid credentials."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_create_user_invalid_password(client: TestClient):
    """Test user creation with invalid password."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "invalidpass@example.com",
            "password": "123",  # Password troppo corta
            "full_name": "Invalid Pass User"
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data)

def test_get_current_user(client: TestClient):
    """Test getting current user info."""
    # Create user and login
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "current@example.com",
            "password": "Test123!@#",
            "full_name": "Current User"
        }
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "current@example.com",
            "password": "Test123!@#"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user info
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["full_name"] == "Current User"

def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user info without token."""
    response = client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401

def test_update_user(client: TestClient):
    """Test updating user information."""
    # Create user and login
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "update@example.com",
            "password": "Test123!@#",
            "full_name": "Update User"
        }
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "update@example.com",
            "password": "Test123!@#"
        }
    )
    token = login_response.json()["access_token"]
    
    # Update user
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        json={
            "full_name": "Updated Name"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

def test_update_user_unauthorized(client: TestClient):
    """Test updating user without token."""
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        json={
            "full_name": "Updated Name"
        }
    )
    assert response.status_code == 401

def test_update_user_invalid_password(client: TestClient):
    """Test updating user with invalid password."""
    # Create user and login
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "updatepass@example.com",
            "password": "Test123!@#",
            "full_name": "Update Pass User"
        }
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={
            "username": "updatepass@example.com",
            "password": "Test123!@#"
        }
    )
    token = login_response.json()["access_token"]
    
    # Try to update with invalid password
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        json={
            "password": "weak"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data) 