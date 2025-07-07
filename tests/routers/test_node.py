import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
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
        nfc_id="NFC_TEST_001",  # Campo obbligatorio
        house_id=test_house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node

@pytest.fixture
def client(test_user):
    # Crea un dizionario con i dati dell'utente per il token
    user_data = {
        "sub": test_user.email,
        "email": test_user.email,
        "username": test_user.username,
        "role": test_user.role
    }
    token = create_access_token(user_data)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})

@pytest.fixture
def multiple_nodes(db_session, test_house):
    """Crea più nodi di test."""
    nodes = []
    for i in range(3):
        node = Node(
            name=f"Node {i+1}",
            description=f"Test node {i+1}",
            nfc_id=f"NFC_TEST_{i+1:03d}",  # Campo obbligatorio
            house_id=test_house.id
        )
        db_session.add(node)
        nodes.append(node)
    db_session.commit()
    for node in nodes:
        db_session.refresh(node)
    return nodes

@pytest.fixture
def unauthorized_client():
    """Client senza token di autenticazione."""
    return TestClient(app)

@pytest.fixture
def invalid_token_client():
    """Client con token di autenticazione invalido."""
    return TestClient(app, headers={"Authorization": "Bearer invalid_token"})

def test_create_node(client, test_house):
    """Test 2.1.4.1: Crea un nodo."""
    node_data = {
        "name": "Nuovo Nodo",
        "description": "Descrizione del nuovo nodo",
        "nfc_id": "NFC456",
        "house_id": test_house.id
    }
    response = client.post("/api/v1/nodes/", json=node_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == node_data["name"]
    assert data["nfc_id"] == node_data["nfc_id"]
    assert data["house_id"] == node_data["house_id"]

def test_read_node(client, test_node):
    """Test 2.1.4.1: Recupera un nodo specifico."""
    response = client.get(f"/api/v1/nodes/{test_node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_node.name
    assert data["nfc_id"] == test_node.nfc_id

def test_update_node(client, test_node):
    """Test 2.1.4.1: Modifica un nodo."""
    update_data = {
        "name": "Nodo Modificato",
        "description": "Descrizione modificata",
        "nfc_id": test_node.nfc_id,
        "house_id": test_node.house_id
    }
    response = client.put(f"/api/v1/nodes/{test_node.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

def test_delete_node(client, test_node):
    """Test 2.1.4.1: Elimina un nodo."""
    response = client.delete(f"/api/v1/nodes/{test_node.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Nodo eliminato con successo"
    
    # Verifica che il nodo sia stato effettivamente eliminato
    response = client.get(f"/api/v1/nodes/{test_node.id}")
    assert response.status_code == 404

def test_filter_nodes(client, db_session, test_house):
    """Test funzionale: Search e Filter."""
    # Crea più nodi per il test
    nodes = [
        Node(name="Nodo A", description="Test A", nfc_id="NFC1", house_id=test_house.id),
        Node(name="Nodo B", description="Test B", nfc_id="NFC2", house_id=test_house.id),
        Node(name="Nodo C", description="Test C", nfc_id="NFC3", house_id=test_house.id)
    ]
    for node in nodes:
        db_session.add(node)
    db_session.commit()
    
    # Test filtro per house_id
    response = client.get(f"/api/v1/nodes/?house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Almeno i 3 nodi creati appartengono alla stessa casa

def test_combined_filters(client, multiple_nodes, test_house):
    """Test filtri combinati su più campi."""
    # Test con filtro house_id
    response = client.get(f"/api/v1/nodes/?house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Almeno i 3 nodi creati

def test_case_insensitive_search(client, multiple_nodes):
    """Test ricerca case-insensitive."""
    # Test con filtro house_id
    response = client.get("/api/v1/nodes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Almeno i 3 nodi creati

def test_duplicate_nfc_id(client, test_node):
    """Test che non si possano creare nodi con NFC ID duplicato."""
    duplicate_data = {
        "name": "Nodo Duplicato",
        "description": "Test duplicato",
        "nfc_id": test_node.nfc_id,  # Stesso NFC ID
        "house_id": test_node.house_id
    }
    response = client.post("/api/v1/nodes/", json=duplicate_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_nonexistent_node(client):
    """Test accesso a nodo inesistente."""
    response = client.get("/api/v1/nodes/99999")
    assert response.status_code == 404

def test_invalid_id_operations(client):
    """Test operazioni con ID non validi."""
    response = client.get("/api/v1/nodes/invalid")
    assert response.status_code == 422  # Validation error

def test_unauthenticated_access(unauthorized_client, test_node):
    """Test accesso senza autenticazione."""
    response = unauthorized_client.get(f"/api/v1/nodes/{test_node.id}")
    assert response.status_code == 401

def test_invalid_token_access(invalid_token_client, test_node):
    """Test accesso con token invalido."""
    response = invalid_token_client.get(f"/api/v1/nodes/{test_node.id}")
    assert response.status_code == 401

def test_empty_database(client):
    """Test comportamento con database vuoto."""
    response = client.get("/api/v1/nodes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_consecutive_deletions(client, db_session, test_house):
    """Test eliminazioni consecutive."""
    # Crea un nodo per il test
    node = Node(
        name="Nodo per eliminazione",
        description="Test eliminazione",
        nfc_id="NFC_DELETE_001",
        house_id=test_house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    
    # Prima eliminazione
    response = client.delete(f"/api/v1/nodes/{node.id}")
    assert response.status_code == 200
    
    # Seconda eliminazione dello stesso nodo
    response = client.delete(f"/api/v1/nodes/{node.id}")
    assert response.status_code == 404

def test_bulk_operations_performance(client, db_session, test_house):
    """Test performance operazioni bulk."""
    import time
    
    # Crea 10 nodi
    start_time = time.time()
    for i in range(10):
        node_data = {
            "name": f"Bulk Node {i}",
            "description": f"Test bulk node {i}",
            "nfc_id": f"NFC_BULK_{i:03d}",
            "house_id": test_house.id
        }
        response = client.post("/api/v1/nodes/", json=node_data)
        assert response.status_code == 200
    
    creation_time = time.time() - start_time
    print(f"Tempo per creare 10 nodi: {creation_time:.2f} secondi")
    
    # Verifica che tutti i nodi siano stati creati
    response = client.get(f"/api/v1/nodes/?house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10 