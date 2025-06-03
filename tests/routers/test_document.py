import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.models.house import House
from app.models.node import Node
from app.core.auth import create_access_token

client = TestClient(app)

@pytest.fixture
def test_user(db: Session):
    user = User(username="testuser", email="test@example.com", hashed_password="testpass")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_house(db: Session, test_user):
    house = House(name="Test House", address="Test Address", owner_id=test_user.id)
    db.add(house)
    db.commit()
    db.refresh(house)
    return house

@pytest.fixture
def test_node(db: Session, test_house):
    node = Node(name="Test Node", nfc_id="TEST123", house_id=test_house.id)
    db.add(node)
    db.commit()
    db.refresh(node)
    return node

@pytest.fixture
def test_document(db: Session, test_user, test_house):
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="/documents/test.pdf",
        checksum="abc123",
        description="Test document description",
        author_id=test_user.id,
        house_id=test_house.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

@pytest.fixture
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}

def test_create_document(test_user, test_house, auth_headers):
    """Test creating a new document"""
    document_data = {
        "name": "New Document",
        "type": "application/pdf",
        "size": 2048,
        "path": "/documents/new.pdf",
        "checksum": "def456",
        "description": "New document description",
        "house_id": test_house.id
    }
    
    response = client.post("/documents/", json=document_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == document_data["name"]
    assert data["author_id"] == test_user.id
    assert data["house_id"] == test_house.id

def test_read_document(test_document, auth_headers):
    """Test reading a specific document"""
    response = client.get(f"/documents/{test_document.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_document.id
    assert data["name"] == test_document.name

def test_read_documents(test_document, auth_headers):
    """Test listing documents with filters"""
    # Test basic listing
    response = client.get("/documents/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    # Test filtering by house_id
    response = client.get(f"/documents/?house_id={test_document.house_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(doc["house_id"] == test_document.house_id for doc in data)
    
    # Test search functionality
    response = client.get(f"/documents/?search={test_document.name}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(test_document.name.lower() in doc["name"].lower() for doc in data)

def test_update_document(test_document, auth_headers):
    """Test updating a document"""
    update_data = {
        "name": "Updated Document",
        "description": "Updated description"
    }
    
    response = client.put(f"/documents/{test_document.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["type"] == test_document.type  # Unchanged field

def test_delete_document(test_document, auth_headers):
    """Test deleting a document"""
    response = client.delete(f"/documents/{test_document.id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify document is deleted
    response = client.get(f"/documents/{test_document.id}", headers=auth_headers)
    assert response.status_code == 404

def test_document_not_found(auth_headers):
    """Test accessing non-existent document"""
    response = client.get("/documents/999", headers=auth_headers)
    assert response.status_code == 404

def test_unauthorized_access():
    """Test accessing endpoints without authentication"""
    response = client.get("/documents/")
    assert response.status_code == 401

def test_document_with_node(test_user, test_node, auth_headers):
    """Test creating and retrieving document with node association"""
    document_data = {
        "name": "Node Document",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/node.pdf",
        "checksum": "ghi789",
        "description": "Document for node",
        "node_id": test_node.id
    }
    
    # Create document
    response = client.post("/documents/", json=document_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] == test_node.id
    
    # Retrieve document
    response = client.get(f"/documents/?node_id={test_node.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(doc["node_id"] == test_node.id for doc in data) 