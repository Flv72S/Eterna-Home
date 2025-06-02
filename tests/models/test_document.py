import pytest
from datetime import datetime, timezone
from sqlmodel import Session
from app.models.document import Document
from app.models.user import User
from app.models.house import House
from app.models.node import Node

def test_create_document(db: Session):
    """Test 2.1.5.1: Verifica creazione documento."""
    document = Document(
        name="test_doc.pdf",
        type="application/pdf",
        size=1024,
        path="/documents/test.pdf",
        checksum="a1b2c3d4e5f6"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    assert document.id is not None
    assert document.name == "test_doc.pdf"
    assert document.type == "application/pdf"
    assert document.size == 1024
    assert document.path == "/documents/test.pdf"
    assert document.checksum == "a1b2c3d4e5f6"
    assert isinstance(document.upload_date, datetime)

def test_document_house_relationship(db: Session):
    """Test 2.1.5.2: Verifica relazione Document-House."""
    # Crea un utente
    user = User(username="testuser", email="test@example.com", hashed_password="testpass")
    db.add(user)
    db.commit()
    
    # Crea una casa
    house = House(name="Test House", address="Test Address", owner_id=user.id)
    db.add(house)
    db.commit()
    
    # Crea un documento associato alla casa
    document = Document(
        name="house_doc.pdf",
        type="application/pdf",
        size=2048,
        path="/documents/house.pdf",
        checksum="b2c3d4e5f6g7",
        house_id=house.id,
        author_id=user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    assert document.house_id == house.id
    assert document.house is not None
    assert document.house.name == "Test House"
    assert document.author_id == user.id
    assert document.author is not None
    assert document.author.username == "testuser"

def test_document_node_relationship(db: Session):
    """Test 2.1.5.2: Verifica relazione Document-Node."""
    # Crea un utente
    user = User(username="testuser", email="test@example.com", hashed_password="testpass")
    db.add(user)
    db.commit()
    
    # Crea una casa
    house = House(name="Test House", address="Test Address", owner_id=user.id)
    db.add(house)
    db.commit()
    
    # Crea un nodo
    node = Node(name="Test Node", nfc_id="NFC123", house_id=house.id)
    db.add(node)
    db.commit()
    
    # Crea un documento associato al nodo
    document = Document(
        name="node_doc.pdf",
        type="application/pdf",
        size=3072,
        path="/documents/node.pdf",
        checksum="c3d4e5f6g7h8",
        node_id=node.id,
        author_id=user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    assert document.node_id == node.id
    assert document.node is not None
    assert document.node.name == "Test Node"
    assert document.author_id == user.id
    assert document.author is not None
    assert document.author.username == "testuser"

def test_document_optional_relationships(db: Session):
    """Test 2.1.5.2: Verifica che le relazioni house_id e node_id siano opzionali."""
    document = Document(
        name="standalone_doc.pdf",
        type="application/pdf",
        size=4096,
        path="/documents/standalone.pdf",
        checksum="d4e5f6g7h8i9"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    assert document.house_id is None
    assert document.node_id is None
    assert document.house is None
    assert document.node is None 