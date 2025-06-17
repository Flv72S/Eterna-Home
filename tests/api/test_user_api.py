import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session
from app.core.config import settings
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

# Configurazione del database di test
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "postgresql://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test",
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    with Session(engine) as session:
        yield session

@pytest_asyncio.fixture(name="async_client")
async def async_client_fixture(session: Session):
    async def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="user_create")
def user_create_fixture():
    return UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User",
        username="testuser"
    )

@pytest_asyncio.fixture(name="user")
async def user_fixture(async_client: AsyncClient, user_create: UserCreate):
    response = await async_client.post("/api/v1/auth/register", json=user_create.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

async def test_create_user_success(async_client: AsyncClient, session: Session):
    """Test successful user creation."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    response = await async_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "hashed_password" not in data
    
    # Verify user was created in database
    db_user = session.exec(select(User).where(User.email == user_data["email"])).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]
    assert db_user.username == user_data["username"]
    assert db_user.full_name == user_data["full_name"]

async def test_create_user_duplicate_email(async_client: AsyncClient, session: Session):
    """Test user creation with duplicate email."""
    # Create initial user
    user_data = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "TestPassword123!",
        "full_name": "Test User 1"
    }
    await async_client.post("/api/v1/auth/register", json=user_data)
    
    # Try to create another user with same email
    duplicate_user = {
        "email": "test@example.com",
        "username": "testuser2",
        "password": "TestPassword123!",
        "full_name": "Test User 2"
    }
    response = await async_client.post("/api/v1/auth/register", json=duplicate_user)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Email già registrata" in response.json()["detail"]

async def test_update_user_success(async_client: AsyncClient, session: Session):
    """Test successful user update."""
    # Create initial user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    response = await async_client.post("/api/v1/auth/register", json=user_data)
    user_id = response.json()["id"]
    
    # Update user
    update_data = {
        "full_name": "Updated Test User",
        "email": "updated@example.com"
    }
    response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]
    
    # Verify database was updated
    db_user = session.get(User, user_id)
    assert db_user.full_name == update_data["full_name"]
    assert db_user.email == update_data["email"]

async def test_update_user_not_found(async_client: AsyncClient):
    """Test updating non-existent user."""
    update_data = {
        "full_name": "Updated Test User"
    }
    response = await async_client.put("/api/v1/users/999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_update_user_duplicate_email(async_client: AsyncClient, session: Session):
    """Test updating user with duplicate email."""
    # Create two users
    user1_data = {
        "email": "user1@example.com",
        "username": "user1",
        "password": "TestPassword123!",
        "full_name": "User 1"
    }
    user2_data = {
        "email": "user2@example.com",
        "username": "user2",
        "password": "TestPassword123!",
        "full_name": "User 2"
    }
    
    response1 = await async_client.post("/api/v1/auth/register", json=user1_data)
    response2 = await async_client.post("/api/v1/auth/register", json=user2_data)
    
    user1_id = response1.json()["id"]
    
    # Try to update user1 with user2's email
    update_data = {
        "email": user2_data["email"]
    }
    response = await async_client.put(f"/api/v1/users/{user1_id}", json=update_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Email già registrata" in response.json()["detail"]

async def test_get_user_success(async_client: AsyncClient, user: dict):
    """Test successful user retrieval."""
    response = await async_client.get(f"/api/v1/users/{user['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user["id"]
    assert data["email"] == user["email"]
    assert data["full_name"] == user["full_name"]
    assert data["username"] == user["username"]
    assert "hashed_password" not in data

async def test_get_user_not_found(async_client: AsyncClient):
    """Test retrieving non-existent user."""
    response = await async_client.get("/api/v1/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Utente non trovato"

async def test_get_users_pagination(async_client: AsyncClient, session: Session):
    """Test user list pagination."""
    # Create 15 test users
    for i in range(15):
        user_data = {
            "email": f"test{i}@example.com",
            "username": f"testuser{i}",
            "password": "TestPassword123!",
            "full_name": f"Test User {i}"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)

    # Test first page (limit=10)
    response = await async_client.get("/api/v1/users/?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 10

    # Test second page
    response = await async_client.get("/api/v1/users/?skip=10&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5  # Only 5 users left

async def test_delete_user_success(async_client: AsyncClient, user: dict):
    """Test successful user deletion."""
    # Get user ID from the created user
    user_id = user["id"]
    
    # Delete the user
    response = await async_client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify user was deleted
    response = await async_client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_delete_user_not_found(async_client: AsyncClient):
    """Test deleting non-existent user."""
    response = await async_client.delete("/api/v1/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND 