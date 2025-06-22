import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User
from app.models.house import House
from app.core.auth import create_access_token
from app.core.security import get_password_hash
from app.models.enums import UserRole

def test_create_house_authenticated(client: TestClient, db_session):
    """Test creazione casa con utente autenticato."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Crea casa
    house_data = {
        "name": "Test House",
        "address": "123 Test Street",
        "description": "A test house"
    }
    
    response = client.post(
        "/api/v1/houses/",
        json=house_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test House"
    assert data["address"] == "123 Test Street"
    assert data["owner_id"] == user.id

def test_list_houses_authenticated(client: TestClient, db_session):
    """Test listaggio case con utente autenticato."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea alcune case
    house1 = House(name="House 1", address="Address 1", owner_id=user.id)
    house2 = House(name="House 2", address="Address 2", owner_id=user.id)
    db_session.add_all([house1, house2])
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Lista case
    response = client.get(
        "/api/v1/houses/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(h["name"] == "House 1" for h in data)
    assert any(h["name"] == "House 2" for h in data)

def test_get_house_authenticated(client: TestClient, db_session):
    """Test ottenimento casa specifica con utente autenticato."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea una casa
    house = House(name="Test House", address="Test Address", owner_id=user.id)
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Ottieni casa
    response = client.get(
        f"/api/v1/houses/{house.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test House"
    assert data["address"] == "Test Address"
    assert data["owner_id"] == user.id

def test_update_house_authenticated(client: TestClient, db_session):
    """Test aggiornamento casa con utente autenticato."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea una casa
    house = House(name="Original Name", address="Original Address", owner_id=user.id)
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Aggiorna casa
    update_data = {
        "name": "Updated Name",
        "address": "Updated Address"
    }
    
    response = client.put(
        f"/api/v1/houses/{house.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["address"] == "Updated Address"

def test_delete_house_authenticated(client: TestClient, db_session):
    """Test eliminazione casa con utente autenticato."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea una casa
    house = House(name="Test House", address="Test Address", owner_id=user.id)
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Elimina casa
    response = client.delete(
        f"/api/v1/houses/{house.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verifica che la casa sia stata eliminata
    response = client.get(
        f"/api/v1/houses/{house.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_house_field_filtering(client: TestClient, db_session):
    """Test filtraggio case per campi specifici."""
    # Crea un utente di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea case con diversi nomi
    house1 = House(name="Villa Bianca", address="Via Roma 1", owner_id=user.id)
    house2 = House(name="Casa Rossa", address="Via Milano 2", owner_id=user.id)
    house3 = House(name="Palazzo Verde", address="Via Napoli 3", owner_id=user.id)
    db_session.add_all([house1, house2, house3])
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Filtra per nome
    response = client.get(
        "/api/v1/houses/?name=Villa",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Villa Bianca"

def test_house_endpoints_unauthenticated(client: TestClient):
    """Test 2.1.2.2: Verifica che l'accesso agli endpoint senza autenticazione restituisca 401."""
    # Test POST /houses
    response = client.post("/houses", json={"name": "Test", "address": "Test"})
    assert response.status_code == 401
    
    # Test GET /houses
    response = client.get("/houses")
    assert response.status_code == 401
    
    # Test GET /houses/{id}
    response = client.get("/houses/1")
    assert response.status_code == 401
    
    # Test PUT /houses/{id}
    response = client.put("/houses/1", json={"name": "Test", "address": "Test"})
    assert response.status_code == 401
    
    # Test DELETE /houses/{id}
    response = client.delete("/houses/1")
    assert response.status_code == 401 