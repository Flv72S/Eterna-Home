import pytest
from sqlalchemy import inspect
from sqlmodel import Session
from app.models.node import Node
from app.models.house import House

def test_node_migration(db: Session):
    """Test 2.1.3.1: Verifica che la tabella node sia creata con i vincoli richiesti."""
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    assert "node" in tables
    columns = [col["name"] for col in inspector.get_columns("node")]
    for col in ["id", "name", "description", "nfc_id", "house_id"]:
        assert col in columns
    
    # Verifica vincolo UNIQUE su nfc_id
    uniques = [c["name"] for c in inspector.get_unique_constraints("node")]
    assert any("nfc_id" in u for u in uniques)
    
    # Verifica indice su nfc_id
    indexes = [idx["name"] for idx in inspector.get_indexes("node")]
    assert any("ix_node_nfc_id" in idx for idx in indexes)

def test_node_house_relationship(db: Session):
    """Test 2.1.3.2: Verifica la relazione tra Node e House."""
    house = House(name="Casa Test", address="Via Test 1", owner_id=1)
    db.add(house)
    db.commit()
    db.refresh(house)
    node = Node(name="Nodo1", nfc_id="NFC123", house_id=house.id)
    db.add(node)
    db.commit()
    db.refresh(node)
    # Relazione diretta
    assert node.house_id == house.id
    # Relazione ORM
    assert node.house is not None
    assert node.house.name == house.name 