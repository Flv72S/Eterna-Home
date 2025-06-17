"""Test user endpoints and functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session
from app.utils.password import get_password_hash

@pytest.fixture(name="client")
def client_fixture(test_db_session: Session):
    def get_session_override():
        return test_db_session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_user(client: TestClient):
    """Test creating a new user."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "hashed_password" not in data

def test_create_user_duplicate_email(client: TestClient, test_db_session: Session):
    """Test creating a user with duplicate email."""
    # Create first user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    # Try to create second user with same email
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()

def test_create_user_invalid_email(client: TestClient):
    """Test creating a user with invalid email."""
    user_data = {
        "email": "invalid-email",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_create_user_short_password(client: TestClient):
    """Test creating a user with short password."""
    user_data = {
        "email": "test@example.com",
        "password": "short",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]

def test_get_current_user(client: TestClient, test_db_session: Session):
    """Test getting current user profile."""
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        full_name="Test User"
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get user profile
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert "hashed_password" not in data

def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()

def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "could not validate credentials" in response.json()["detail"].lower()