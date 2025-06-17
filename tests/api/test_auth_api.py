"""Test authentication endpoints."""
import pytest
from httpx import AsyncClient
from fastapi import status

from app.models.user import User
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio

async def test_login_success(async_client: AsyncClient, user: dict):
    """Test successful login."""
    response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": user["email"],
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

async def test_login_invalid_credentials(async_client: AsyncClient):
    """Test login with invalid credentials."""
    response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": "wrong@email.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_refresh_token(async_client: AsyncClient, user: dict):
    """Test token refresh."""
    # First login to get initial token
    login_response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": user["email"],
            "password": "testpassword123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    initial_token = login_response.json()["access_token"]

    # Try to refresh the token
    response = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {initial_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != initial_token

async def test_logout(async_client: AsyncClient, user: dict):
    """Test logout functionality."""
    # First login to get token
    login_response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": user["email"],
            "password": "testpassword123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]

    # Try to logout
    response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify token is no longer valid
    verify_response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED 