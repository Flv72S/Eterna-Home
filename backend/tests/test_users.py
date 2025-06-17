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

def test_get_user(db_session):
    """Test retrieving a user by ID"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Get user by ID
    retrieved_user = crud.get_user(db_session, user.id)
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.full_name == user_data["full_name"]

def test_get_user_by_email(db_session):
    """Test retrieving a user by email"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Get user by email
    retrieved_user = crud.get_user_by_email(db_session, user_data["email"])
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.full_name == user_data["full_name"]

def test_authenticate_user(db_session):
    """Test user authentication"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Test correct credentials
    authenticated_user = crud.authenticate_user(
        db_session, user_data["email"], user_data["password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    
    # Test incorrect password
    wrong_user = crud.authenticate_user(
        db_session, user_data["email"], "wrongpassword"
    )
    assert wrong_user is None
    
    # Test non-existent user
    nonexistent_user = crud.authenticate_user(
        db_session, "nonexistent@example.com", "anypassword"
    )
    assert nonexistent_user is None

def test_get_users(db_session):
    """Test retrieving multiple users"""
    # Create test users
    users_data = [
        {
            "email": "test1@example.com",
            "password": "testpassword123",
            "full_name": "Test User 1"
        },
        {
            "email": "test2@example.com",
            "password": "testpassword123",
            "full_name": "Test User 2"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = crud.create_user(db_session, user_data)
        created_users.append(user)
    
    # Get all users
    users = crud.get_users(db_session)
    
    # Verify users were retrieved correctly
    assert len(users) >= len(created_users)  # There might be other users in the database
    for created_user in created_users:
        assert any(u.id == created_user.id for u in users)
        assert any(u.email == created_user.email for u in users)
        assert any(u.full_name == created_user.full_name for u in users)

def test_update_user(db_session):
    """Test updating a user"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Update user data
    update_data = {
        "full_name": "Updated User",
        "email": "updated@example.com"
    }
    
    # Update user
    updated_user = crud.update_user(db_session, user.id, update_data)
    
    # Verify user was updated correctly
    assert updated_user is not None
    assert updated_user.id == user.id
    assert updated_user.email == update_data["email"]
    assert updated_user.full_name == update_data["full_name"]
    
    # Verify changes are in database
    db_user = db_session.query(models.User).filter(models.User.id == user.id).first()
    assert db_user is not None
    assert db_user.email == update_data["email"]
    assert db_user.full_name == update_data["full_name"]

def test_delete_user(db_session):
    """Test deleting a user"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = crud.create_user(db_session, user_data)
    
    # Delete user
    deleted_user = crud.delete_user(db_session, user.id)
    
    # Verify user was deleted correctly
    assert deleted_user is not None
    assert deleted_user.id == user.id
    
    # Verify user no longer exists in database
    db_user = db_session.query(models.User).filter(models.User.id == user.id).first()
    assert db_user is None 