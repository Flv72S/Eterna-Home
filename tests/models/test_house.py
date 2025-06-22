import pytest
from sqlalchemy import inspect
from sqlmodel import Session

from app.models.house import House
from app.models.user import User

def test_house_migration(db_session):
    """Test che la tabella house sia stata creata correttamente."""
    inspector = inspect(db_session.get_bind())
    tables = inspector.get_table_names()
    assert "house" in tables
    
    # Verifica le colonne
    columns = [col["name"] for col in inspector.get_columns("house")]
    expected_columns = ["id", "name", "address", "owner_id", "created_at", "updated_at"]
    for col in expected_columns:
        assert col in columns

def test_house_owner_relationship(db_session):
    """Test relazione casa-proprietario."""
    # Crea un utente
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
    
    # Crea una casa
    house = House(
        name="User House",
        address="456 User Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Verifica relazione
    assert house.owner_id == user.id
    assert house.owner == user
    assert house in user.houses 