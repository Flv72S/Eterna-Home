import pytest
from fastapi.testclient import TestClient

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_password_hash

def test_create_user(client: TestClient):
    """Test creazione utente."""
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "is_active": True,
        "is_superuser": False
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert data["is_active"] == user_data["is_active"]
    assert data["is_superuser"] == user_data["is_superuser"]
    assert "id" in data

def test_create_user_duplicate_email(client: TestClient):
    """Test creazione utente con email duplicata."""
    # Crea primo utente
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "is_active": True,
        "is_superuser": False
    }
    client.post("/api/v1/users/", json=user_data)
    
    # Prova a creare un secondo utente con la stessa email
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email già registrata"

def test_read_users(client: TestClient):
    """Test lettura lista utenti."""
    # Crea alcuni utenti di test
    users = [
        {"email": f"user{i}@example.com", "password": "password123"} 
        for i in range(3)
    ]
    for user_data in users:
        client.post("/api/v1/users/", json=user_data)
    
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("email" in user for user in data)
    assert all("password" not in user for user in data)

def test_read_user(client: TestClient):
    """Test lettura singolo utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Leggi l'utente creato
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert data["id"] == user_id

def test_read_user_not_found(client: TestClient):
    """Test lettura utente non esistente."""
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_update_user(client: TestClient):
    """Test aggiornamento utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Aggiorna l'utente
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123"
    }
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    assert "password" not in data

def test_update_user_not_found(client: TestClient):
    """Test aggiornamento utente non esistente."""
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123"
    }
    response = client.put("/api/v1/users/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_delete_user(client: TestClient):
    """Test eliminazione utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Elimina l'utente
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204
    
    # Verifica che l'utente sia stato eliminato
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404

def test_delete_user_not_found(client: TestClient):
    """Test eliminazione utente non esistente."""
    response = client.delete("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato" 