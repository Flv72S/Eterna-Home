import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.node import Node
from app.models.house import House
from app.models.user import User
from app.api.v1.auth import create_access_token
import time
from app.models.enums import UserRole
from app.utils.password import get_password_hash

@pytest.fixture
def test_user(db_session):
    """Crea un utente di test."""
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
        node_type="sensor",
        location="Living Room",
        house_id=test_house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node

@pytest.fixture
def client(test_user):
    token = create_access_token(test_user)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})

@pytest.fixture
def multiple_nodes(db_session, test_house):
    """Crea più nodi di test."""
    nodes = []
    for i in range(3):
        node = Node(
            name=f"Node {i+1}",
            node_type="sensor" if i % 2 == 0 else "actuator",
            location=f"Room {i+1}",
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
        "nfc_id": "NFC456",
        "house_id": test_house.id
    }
    response = client.post("/nodes/", json=node_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == node_data["name"]
    assert data["nfc_id"] == node_data["nfc_id"]
    assert data["house_id"] == node_data["house_id"]

def test_read_node(client, test_node):
    """Test 2.1.4.1: Recupera un nodo specifico."""
    response = client.get(f"/nodes/{test_node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_node.name
    assert data["nfc_id"] == test_node.nfc_id

def test_update_node(client, test_node):
    """Test 2.1.4.1: Modifica un nodo."""
    update_data = {
        "name": "Nodo Modificato",
        "nfc_id": test_node.nfc_id,
        "house_id": test_node.house_id
    }
    response = client.put(f"/nodes/{test_node.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

def test_delete_node(client, test_node):
    """Test 2.1.4.1: Elimina un nodo."""
    response = client.delete(f"/nodes/{test_node.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Nodo eliminato con successo"
    
    # Verifica che il nodo sia stato effettivamente eliminato
    response = client.get(f"/nodes/{test_node.id}")
    assert response.status_code == 404

def test_filter_nodes(client, db_session, test_house):
    """Test funzionale: Search e Filter."""
    # Crea più nodi per il test
    nodes = [
        Node(name="Nodo A", nfc_id="NFC1", house_id=test_house.id),
        Node(name="Nodo B", nfc_id="NFC2", house_id=test_house.id),
        Node(name="Nodo C", nfc_id="NFC3", house_id=test_house.id)
    ]
    for node in nodes:
        db_session.add(node)
    db_session.commit()
    
    # Test filtro per nome
    response = client.get("/nodes/?name=Nodo A")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Nodo A"
    
    # Test filtro per nfc_id
    response = client.get("/nodes/?nfc_id=NFC2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nfc_id"] == "NFC2"
    
    # Test filtro per house_id
    response = client.get(f"/nodes/?house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Tutti i nodi appartengono alla stessa casa
    
    # Test filtro combinato
    response = client.get(f"/nodes/?name=Nodo&house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Tutti i nodi hanno "Nodo" nel nome 

def test_combined_filters(client, multiple_nodes, test_house):
    """Test filtri combinati su più campi."""
    # Test con tutti i filtri
    response = client.get(f"/nodes/?name=Nodo A&nfc_id=NFC1&house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Nodo A"
    assert data[0]["nfc_id"] == "NFC1"

    # Test con filtri parziali
    response = client.get(f"/nodes/?name=Nodo&house_id={test_house.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Tutti i nodi hanno "Nodo" nel nome

def test_case_insensitive_search(client, multiple_nodes):
    """Test ricerca case-insensitive."""
    # Test con nome in minuscolo
    response = client.get("/nodes/?name=nodo a")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Nodo A"

    # Test con NFC ID in minuscolo
    response = client.get("/nodes/?nfc_id=nfc1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nfc_id"] == "NFC1"

def test_duplicate_nfc_id(client, test_node):
    """Test creazione nodo con nfc_id duplicato."""
    node_data = {
        "name": "Nuovo Nodo",
        "nfc_id": test_node.nfc_id,  # Usa lo stesso nfc_id del nodo esistente
        "house_id": test_node.house_id
    }
    response = client.post("/nodes/", json=node_data)
    assert response.status_code == 400
    assert "nfc_id" in response.json()["detail"].lower()

def test_nonexistent_node(client):
    """Test accesso a nodo non esistente."""
    response = client.get("/nodes/99999")
    assert response.status_code == 404
    assert "non trovato" in response.json()["detail"].lower()

def test_invalid_id_operations(client):
    """Test operazioni PUT/DELETE con ID errato."""
    # PUT con ID errato
    response = client.put("/nodes/99999", json={"name": "Test"})
    assert response.status_code == 404

    # DELETE con ID errato
    response = client.delete("/nodes/99999")
    assert response.status_code == 404

def test_unauthenticated_access(unauthorized_client, test_node):
    """Test accesso non autenticato."""
    # GET
    response = unauthorized_client.get(f"/nodes/{test_node.id}")
    assert response.status_code == 401

    # POST
    response = unauthorized_client.post("/nodes/", json={})
    assert response.status_code == 401

    # PUT
    response = unauthorized_client.put(f"/nodes/{test_node.id}", json={})
    assert response.status_code == 401

    # DELETE
    response = unauthorized_client.delete(f"/nodes/{test_node.id}")
    assert response.status_code == 401

def test_invalid_token_access(invalid_token_client, test_node):
    """Test accesso con token invalido."""
    # GET
    response = invalid_token_client.get(f"/nodes/{test_node.id}")
    assert response.status_code == 401

    # POST
    response = invalid_token_client.post("/nodes/", json={})
    assert response.status_code == 401

def test_empty_database(client):
    """Test con database vuoto."""
    response = client.get("/nodes/")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_consecutive_deletions(client, db_session, test_house):
    """Test rimozione consecutiva di nodi."""
    # Crea due nodi
    node1 = Node(name="Nodo 1", nfc_id="NFC1", house_id=test_house.id)
    node2 = Node(name="Nodo 2", nfc_id="NFC2", house_id=test_house.id)
    db_session.add_all([node1, node2])
    db_session.commit()
    db_session.refresh(node1)
    db_session.refresh(node2)

    # Elimina il primo nodo
    response = client.delete(f"/nodes/{node1.id}")
    assert response.status_code == 200

    # Verifica che il secondo nodo sia ancora accessibile
    response = client.get(f"/nodes/{node2.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Nodo 2"

    # Elimina il secondo nodo
    response = client.delete(f"/nodes/{node2.id}")
    assert response.status_code == 200

    # Verifica che entrambi i nodi siano stati eliminati
    response = client.get("/nodes/")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_bulk_operations_performance(client, db_session, test_house):
    """Test performance con operazioni bulk."""
    # Crea 1000 nodi
    start_time = time.time()
    nodes = []
    for i in range(1000):
        node = Node(
            name=f"Nodo {i}",
            nfc_id=f"NFC{i}",
            house_id=test_house.id
        )
        nodes.append(node)
    db_session.add_all(nodes)
    db_session.commit()
    creation_time = time.time() - start_time

    # Test performance GET con filtro
    start_time = time.time()
    response = client.get(f"/nodes/?house_id={test_house.id}")
    query_time = time.time() - start_time

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1000

    # Verifica che i tempi siano ragionevoli
    assert creation_time < 5.0  # Creazione di 1000 nodi in meno di 5 secondi
    assert query_time < 1.0    # Query con filtro in meno di 1 secondo 