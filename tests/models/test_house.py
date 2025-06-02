import pytest
from sqlalchemy import inspect
from sqlmodel import Session

from app.models.house import House
from app.models.user import User

def test_house_migration(db: Session):
    """Verifica che la tabella house sia creata correttamente."""
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    assert "house" in tables
    
    # Verifica le colonne
    columns = [col["name"] for col in inspector.get_columns("house")]
    expected_columns = ["id", "name", "address", "owner_id", "created_at", "updated_at"]
    for col in expected_columns:
        assert col in columns

def test_house_owner_relationship(db: Session):
    """Verifica la relazione tra House e User."""
    # Crea un utente
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
    
    # Verifica la relazione House -> User
    assert house.owner is not None
    assert house.owner.id == user.id
    assert house.owner.email == user.email
    
    # Verifica la relazione User -> House
    assert len(user.houses) == 1
    assert user.houses[0].id == house.id
    assert user.houses[0].name == house.name 