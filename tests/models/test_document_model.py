import pytest
from datetime import datetime, timezone
from sqlmodel import Session
from app.models.document import Document
from app.models.user import User
from app.models.house import House
from app.models.node import Node

def test_create_document(db_session):
    """Test creazione di un documento base."""
    # Crea utente e casa di test
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea documento
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="/documents/test.pdf",
        checksum="abc123",
        house_id=house.id,
        author_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    assert document.id is not None
    assert document.name == "Test Document"
    assert document.type == "application/pdf"
    assert document.size == 1024
    assert document.house_id == house.id
    assert document.author_id == user.id

def test_document_house_relationship(db_session):
    """Test relazione documento-casa."""
    # Crea utente e casa
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea documento associato alla casa
    document = Document(
        name="House Document",
        type="application/pdf",
        size=2048,
        path="/documents/house.pdf",
        checksum="def456",
        house_id=house.id,
        author_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Verifica relazione
    assert document.house_id == house.id
    assert document.house == house
    assert document in house.documents

def test_document_node_relationship(db_session):
    """Test relazione documento-nodo."""
    # Crea utente, casa e nodo
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    node = Node(
        name="Test Node",
        node_type="sensor",
        location="Living Room",
        house_id=house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    
    # Crea documento associato al nodo
    document = Document(
        name="Node Document",
        type="application/pdf",
        size=1024,
        path="/documents/node.pdf",
        checksum="ghi789",
        house_id=house.id,
        author_id=user.id,
        node_id=node.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Verifica relazione
    assert document.node_id == node.id
    assert document.node == node
    assert document in node.documents

def test_document_optional_relationships(db_session):
    """Test che le relazioni opzionali funzionino correttamente."""
    # Crea utente e casa
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea documento senza nodo (relazione opzionale)
    document = Document(
        name="Optional Document",
        type="application/pdf",
        size=1024,
        path="/documents/optional.pdf",
        checksum="jkl012",
        house_id=house.id,
        author_id=user.id
        # node_id non specificato
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Verifica che il documento sia creato correttamente
    assert document.id is not None
    assert document.node_id is None
    assert document.node is None 