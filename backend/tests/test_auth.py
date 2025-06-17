import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

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

TEST_USER_WEAK_PASSWORD = {
    "email": "test2@example.com",
    "password": "weak",
    "full_name": "Test User 2"
}

TEST_USER_INVALID_EMAIL = {
    "email": "invalid-email",
    "password": "Test123!@#",
    "full_name": "Test User 3"
}

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        # Cleanup
        session.execute(text("DELETE FROM \"user\" CASCADE"))
        session.commit()

def test_register_user_success(client, db_session):
    """Test successful user registration."""
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "id" in data
    assert data["username"] is not None  # Should be auto-generated

def test_register_user_duplicate_email(client, db_session):
    """Test registration with duplicate email."""
    # First registration
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Second registration with same email
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert "Email già registrata" in response.json()["detail"]

def test_register_user_invalid_email(client, db_session):
    """Test registration with invalid email."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_INVALID_EMAIL)
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_register_user_weak_password(client, db_session):
    """Test registration with weak password."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_WEAK_PASSWORD)
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]

def test_login_success(client, db_session):
    """Test successful login."""
    # Register user first
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Try to login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, db_session):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def test_login_disabled_account(client, db_session):
    """Test login with disabled account."""
    # Create disabled user
    user = User(
        email=TEST_USER["email"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Try to login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def test_get_current_user_success(client, db_session):
    """Test getting current user profile."""
    # Register and login
    client.post("/api/v1/auth/register", json=TEST_USER)
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Get profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]

def test_get_current_user_invalid_token(client, db_session):
    """Test getting profile with invalid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_get_current_user_no_token(client, db_session):
    """Test getting profile without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_login_rate_limit(client, db_session):
    """Test rate limiting on login endpoint."""
    # Register user first
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Try to login 6 times (should fail on the 6th attempt)
    for i in range(6):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
        )
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "Troppi tentativi di login" in response.json()["detail"] 