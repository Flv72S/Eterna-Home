import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate

# Utilizziamo la stessa configurazione del database definita in config.py
from app.core.config import settings

def test_create_admin_user():
    client = TestClient(app)
    
    # Dati dell'utente amministratore
    admin_data = {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True
    }
    
    # Chiamata API per creare l'utente
    response = client.post("/api/v1/auth/register", json=admin_data)
    
    # Verifica della risposta
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_data["email"]
    assert data["full_name"] == admin_data["full_name"]
    assert data["is_active"] == admin_data["is_active"]
    assert data["is_superuser"] == admin_data["is_superuser"]
    assert "id" in data
    assert "password" not in data  # La password non deve essere restituita 