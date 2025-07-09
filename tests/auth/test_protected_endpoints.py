import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
import fakeredis
from unittest.mock import patch

from app.main import app
from app.core.redis import redis_client
from app.models.user import User
from app.core.security import create_access_token
from app.core.security import create_access_token as new_create_access_token
from app.core.deps import get_current_user
from app.models.enums import UserRole

@pytest.mark.asyncio
async def test_get_current_user_authenticated(client, db_session):
    """Test che get_current_user funzioni con token valido."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea un token valido
    token = new_create_access_token(data={"sub": user.email})
    
    # Simula una richiesta con il token
    from fastapi import HTTPException
    from unittest.mock import Mock
    
    mock_request = Mock()
    mock_request.headers = {"Authorization": f"Bearer {token}"}
    
    # Testa get_current_user - ora con await
    current_user = await get_current_user(token=token, session=db_session)
    assert current_user.id == user.id
    assert current_user.email == user.email

def test_get_current_user_unauthenticated(client):
    """Test per utente non autenticato."""
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