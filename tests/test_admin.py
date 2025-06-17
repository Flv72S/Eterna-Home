import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.user import UserService
from app.schemas.user import UserCreate

client = TestClient(app)

def test_create_admin_user():
    # Crea un utente admin
    admin_data = {
        "email": "admin@test.com",
        "username": "admin",
        "password": "admin123",
        "is_superuser": True
    }
    
    # Crea l'utente admin
    admin = UserService.create_user(UserCreate(**admin_data))
    print(f"\nAdmin user created: {admin}")
    
    # Verifica che l'utente sia stato creato correttamente
    assert admin is not None
    assert admin.email == admin_data["email"]
    assert admin.username == admin_data["username"]
    assert admin.is_superuser is True

if __name__ == "__main__":
    test_create_admin_user() 