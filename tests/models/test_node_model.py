import pytest
from sqlalchemy import inspect
from sqlmodel import Session
from app.models.node import Node
from app.models.house import House

def test_node_migration(db_session):
    """Test che la tabella node sia stata creata correttamente."""
    from app.models.user import User
    from app.models.house import House
    
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
    
    # Crea un nodo
    node = Node(
        name="Test Node",
        node_type="sensor",
        location="Living Room",
        description="A test node",
        house_id=house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    
    assert node.id is not None
    assert node.name == "Test Node"
    assert node.node_type == "sensor"
    assert node.location == "Living Room"
    assert node.description == "A test node"
    assert node.house_id == house.id

def test_node_house_relationship(db_session):
    """Test relazione nodo-casa."""
    from app.models.user import User
    from app.models.house import House
    
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
    
    # Crea un nodo associato alla casa
    node = Node(
        name="House Node",
        node_type="actuator",
        location="Kitchen",
        house_id=house.id
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    
    # Verifica relazione
    assert node.house_id == house.id
    assert node.house == house
    assert node in house.nodes 