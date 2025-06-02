import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User
from app.models.house import House
from app.core.auth import create_access_token

def test_create_house_authenticated(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica la creazione di una casa da parte di un utente autenticato."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Crea una casa
    house_data = {
        "name": "Casa Test",
        "address": "Via Test 123"
    }
    response = client.post("/houses", json=house_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == house_data["name"]
    assert data["address"] == house_data["address"]
    assert data["owner_id"] == user.id

def test_list_houses_authenticated(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica il recupero della lista delle case dell'utente autenticato."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea alcune case per l'utente
    houses = [
        House(name=f"Casa {i}", address=f"Via Test {i}", owner_id=user.id)
        for i in range(3)
    ]
    for house in houses:
        db.add(house)
    db.commit()
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Recupera la lista delle case
    response = client.get("/houses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3

def test_get_house_authenticated(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica il recupero dei dettagli di una casa."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea una casa
    house = House(
        name="Casa Test",
        address="Via Test 123",
        owner_id=user.id
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Recupera i dettagli della casa
    response = client.get(f"/houses/{house.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == house.name
    assert data["address"] == house.address
    assert data["owner_id"] == user.id

def test_update_house_authenticated(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica l'aggiornamento di una casa."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea una casa
    house = House(
        name="Casa Test",
        address="Via Test 123",
        owner_id=user.id
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Aggiorna la casa
    update_data = {
        "name": "Casa Test Aggiornata",
        "address": "Via Test 456"
    }
    response = client.put(f"/houses/{house.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["address"] == update_data["address"]

def test_delete_house_authenticated(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica l'eliminazione di una casa."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea una casa
    house = House(
        name="Casa Test",
        address="Via Test 123",
        owner_id=user.id
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Elimina la casa
    response = client.delete(f"/houses/{house.id}", headers=headers)
    assert response.status_code == 204
    
    # Verifica che la casa sia stata eliminata
    db.refresh(house)
    assert house not in db

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

def test_house_field_filtering(client: TestClient, db: Session):
    """Test 2.1.2.1: Verifica il field filtering nella lista delle case."""
    # Crea un utente di test
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Crea una casa
    house = House(
        name="Casa Test",
        address="Via Test 123",
        owner_id=user.id
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    
    # Crea il token JWT
    token = create_access_token({"sub": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test field filtering valido
    response = client.get("/houses?fields=name,address", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "name" in data["items"][0]
    assert "address" in data["items"][0]
    assert "id" not in data["items"][0]
    assert "owner_id" not in data["items"][0]
    
    # Test field filtering non valido
    response = client.get("/houses?fields=invalid_field", headers=headers)
    assert response.status_code == 400 