import pytest
from sqlmodel import Session

from app.models.user import User
from app.models.house import House

def test_house_user_relationship_functional(db: Session):
    """Test funzionale per verificare le relazioni ORM tra User e House."""
    # 1. Crea un utente
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 2. Crea una casa associata all'utente
    house = House(
        name="Casa Test",
        address="Via Test 123",
        owner_id=user.id
    )
    db.add(house)
    db.commit()
    
    # 3. Verifica la relazione User -> House
    db.refresh(user)
    assert len(user.houses) == 1
    assert user.houses[0].name == "Casa Test"
    assert user.houses[0].address == "Via Test 123"
    
    # 4. Verifica la relazione House -> User
    db.refresh(house)
    assert house.owner is not None
    assert house.owner.id == user.id
    assert house.owner.username == "testuser"
    assert house.owner.email == "test@example.com" 