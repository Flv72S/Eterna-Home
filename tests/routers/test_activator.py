import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.models.physical_activator import PhysicalActivator, ActivatorType
from app.models.node import Node
from app.models.house import House
from app.models.user import User
from app.core.security import create_access_token
import time
from app.models.enums import UserRole
from app.utils.password import get_password_hash

@pytest.fixture
def test_user(db_session):
    """Crea un utente di test."""
    # Usa timestamp per email e username unici
    timestamp = int(time.time() * 1000)
    user = User(
        email=f"test_{timestamp}@example.com",
        username=f"testuser_{timestamp}",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_house(db_session, test_user):
    """Crea una casa di test."""
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=test_user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def test_node(db_session, test_house):
    """Crea un nodo di test."""
    node = Node(
        name="Test Node",
        description="Test node description",
        nfc_id="NFC_TEST_001",
        house_id=test_house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node

@pytest.fixture
def test_activator(db_session, test_node):
    """Crea un attivatore di test."""
    activator = PhysicalActivator(
        name="Test Activator",
        description="Test activator description",
        activator_type=ActivatorType.NFC,
        node_id=test_node.id,
        is_enabled=True
    )
    db_session.add(activator)
    db_session.commit()
    db_session.refresh(activator)
    return activator

@pytest.fixture
def client(test_user):
    """Crea un client di test con autenticazione."""
    user_data = {
        "sub": test_user.email,
        "email": test_user.email,
        "username": test_user.username,
        "role": test_user.role
    }
    token = create_access_token(user_data)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})

@pytest.fixture
def unauthorized_client():
    """Client senza token di autenticazione."""
    return TestClient(app)

@pytest.fixture
def invalid_token_client():
    """Client con token di autenticazione invalido."""
    return TestClient(app, headers={"Authorization": "Bearer invalid_token"})

def test_create_activator(client, test_node):
    """Test: Crea un nuovo attivatore."""
    activator_data = {
        "name": "Nuovo Attivatore",
        "description": "Descrizione del nuovo attivatore",
        "activator_type": "nfc",
        "node_id": test_node.id,
        "is_enabled": True
    }
    response = client.post("/api/v1/activators/", json=activator_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == activator_data["name"]
    assert data["activator_type"] == activator_data["activator_type"]
    assert data["node_id"] == activator_data["node_id"]

def test_read_activator(client, test_activator):
    """Test: Recupera un attivatore specifico."""
    response = client.get(f"/api/v1/activators/{test_activator.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_activator.name
    assert data["activator_type"] == test_activator.activator_type.value

def test_update_activator(client, test_activator):
    """Test: Modifica un attivatore."""
    update_data = {
        "name": "Attivatore Modificato",
        "description": "Descrizione modificata",
        "activator_type": "ble",
        "node_id": test_activator.node_id,
        "is_enabled": False
    }
    response = client.put(f"/api/v1/activators/{test_activator.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["activator_type"] == update_data["activator_type"]
    assert data["is_enabled"] == update_data["is_enabled"]

def test_delete_activator(client, test_activator):
    """Test: Elimina un attivatore."""
    response = client.delete(f"/api/v1/activators/{test_activator.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Attivatore eliminato con successo"
    
    # Verifica che l'attivatore sia stato effettivamente eliminato
    response = client.get(f"/api/v1/activators/{test_activator.id}")
    assert response.status_code == 404

def test_list_activators(client, db_session, test_node):
    """Test: Lista tutti gli attivatori."""
    # Crea più attivatori per il test
    activators = [
        PhysicalActivator(
            name=f"Attivatore {i}",
            description=f"Test activator {i}",
            activator_type=ActivatorType.NFC,
            node_id=test_node.id,
            is_enabled=True
        )
        for i in range(3)
    ]
    for activator in activators:
        db_session.add(activator)
    db_session.commit()
    
    response = client.get("/api/v1/activators/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Almeno i 3 attivatori creati

def test_activate_activator(client, test_activator):
    """Test: Attiva un attivatore."""
    activation_data = {
        "triggered_by": "test_user",
        "meta_data": {"test": "data"}
    }
    response = client.post(f"/api/v1/activators/{test_activator.id}/activate", json=activation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "activation_id" in data

def test_activate_disabled_activator(client, db_session, test_node):
    """Test: Tentativo di attivazione di un attivatore disabilitato."""
    # Crea un attivatore disabilitato
    disabled_activator = PhysicalActivator(
        name="Attivatore Disabilitato",
        description="Test disabled activator",
        activator_type=ActivatorType.NFC,
        node_id=test_node.id,
        is_enabled=False
    )
    db_session.add(disabled_activator)
    db_session.commit()
    db_session.refresh(disabled_activator)
    
    activation_data = {
        "triggered_by": "test_user",
        "meta_data": {"test": "data"}
    }
    response = client.post(f"/api/v1/activators/{disabled_activator.id}/activate", json=activation_data)
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()

def test_activate_nonexistent_activator(client):
    """Test: Tentativo di attivazione di un attivatore inesistente."""
    activation_data = {
        "triggered_by": "test_user",
        "meta_data": {"test": "data"}
    }
    response = client.post("/api/v1/activators/99999/activate", json=activation_data)
    assert response.status_code == 404

def test_filter_activators_by_type(client, db_session, test_node):
    """Test: Filtra attivatori per tipo."""
    # Crea attivatori di diversi tipi
    nfc_activator = PhysicalActivator(
        name="NFC Activator",
        description="NFC test activator",
        activator_type=ActivatorType.NFC,
        node_id=test_node.id,
        is_enabled=True
    )
    ble_activator = PhysicalActivator(
        name="BLE Activator",
        description="BLE test activator",
        activator_type=ActivatorType.BLE,
        node_id=test_node.id,
        is_enabled=True
    )
    db_session.add_all([nfc_activator, ble_activator])
    db_session.commit()
    
    # Test filtro per tipo NFC
    response = client.get("/api/v1/activators/?activator_type=nfc")
    assert response.status_code == 200
    data = response.json()
    assert all(act["activator_type"] == "nfc" for act in data)

def test_filter_activators_by_node(client, db_session, test_node):
    """Test: Filtra attivatori per nodo."""
    # Crea attivatori per lo stesso nodo
    activators = [
        PhysicalActivator(
            name=f"Activator {i}",
            description=f"Test activator {i}",
            activator_type=ActivatorType.NFC,
            node_id=test_node.id,
            is_enabled=True
        )
        for i in range(3)
    ]
    for activator in activators:
        db_session.add(activator)
    db_session.commit()
    
    # Test filtro per node_id
    response = client.get(f"/api/v1/activators/?node_id={test_node.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(act["node_id"] == test_node.id for act in data)

def test_unauthenticated_access(unauthorized_client, test_activator):
    """Test: Accesso senza autenticazione."""
    response = unauthorized_client.get(f"/api/v1/activators/{test_activator.id}")
    assert response.status_code == 401

def test_invalid_token_access(invalid_token_client, test_activator):
    """Test: Accesso con token invalido."""
    response = invalid_token_client.get(f"/api/v1/activators/{test_activator.id}")
    assert response.status_code == 401

def test_invalid_activator_type(client, test_node):
    """Test: Creazione attivatore con tipo invalido."""
    activator_data = {
        "name": "Attivatore Invalido",
        "description": "Test invalid activator",
        "activator_type": "invalid_type",
        "node_id": test_node.id,
        "is_enabled": True
    }
    response = client.post("/api/v1/activators/", json=activator_data)
    assert response.status_code == 422  # Validation error

def test_activator_with_nonexistent_node(client):
    """Test: Creazione attivatore con nodo inesistente."""
    activator_data = {
        "name": "Attivatore Nodo Inesistente",
        "description": "Test activator with nonexistent node",
        "activator_type": "nfc",
        "node_id": 99999,
        "is_enabled": True
    }
    response = client.post("/api/v1/activators/", json=activator_data)
    assert response.status_code == 404

def test_activator_activation_history(client, test_activator):
    """Test: Recupera la cronologia di attivazione di un attivatore."""
    # Prima attiva l'attivatore alcune volte
    for i in range(3):
        activation_data = {
            "triggered_by": f"user_{i}",
            "meta_data": {"iteration": i}
        }
        client.post(f"/api/v1/activators/{test_activator.id}/activate", json=activation_data)
    
    # Poi recupera la cronologia
    response = client.get(f"/api/v1/activators/{test_activator.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Almeno le 3 attivazioni create 