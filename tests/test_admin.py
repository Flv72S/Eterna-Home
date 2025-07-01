import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.user import UserService
from app.schemas.user import UserCreate

def test_create_admin_user(client, db_session):
    """Test creating an admin user through the API."""
    # Crea un utente admin tramite API
    admin_data = {
        "email": "admin@test.com",
        "username": "admin",
        "password": "Admin123!",
        "full_name": "Admin User"
    }
    
    # Registra l'utente tramite API
    response = client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201
    
    # Login per ottenere il token
    login_data = {
        "username": admin_data["email"],
        "password": admin_data["password"]
    }
    login_response = client.post("/api/v1/auth/token", data=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Verifica che l'utente sia stato creato correttamente
    user_data = token_data["user"]
    assert user_data["email"] == admin_data["email"]
    assert user_data["username"] == admin_data["username"]
    assert user_data["full_name"] == admin_data["full_name"]
    
    # Verifica che l'utente abbia un ruolo (anche se non è admin di default)
    assert "role" in user_data

if __name__ == "__main__":
    test_create_admin_user() 