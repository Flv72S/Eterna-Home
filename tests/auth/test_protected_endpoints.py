import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
import fakeredis
from unittest.mock import patch

from app.main import app
from app.core.redis import redis_client
from app.models.user import User
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for testing."""
    with patch('app.core.redis.redis_client', fakeredis.FakeStrictRedis()):
        yield

def test_get_current_user_authenticated(db: Session):
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    # Test protected endpoint
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert "hashed_password" not in data

def test_get_current_user_unauthenticated():
    # Test without auth header
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Test with invalid token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials" 