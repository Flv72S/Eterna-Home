import pytest
from sqlmodel import Session

from app.models.user import User
from app.models.house import House
from app.models.user_role import UserRole

def test_house_user_relationship_functional(db_session):
    """Test funzionale della relazione casa-utente."""
    # Crea un utente
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        role=UserRole.OWNER.value
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea più case per lo stesso utente
    houses = []
    for i in range(3):
        house = House(
            name=f"House {i+1}",
            address=f"Address {i+1}",
            owner_id=user.id
        )
        db_session.add(house)
        houses.append(house)
    
    db_session.commit()
    for house in houses:
        db_session.refresh(house)
    
    # Verifica relazioni
    assert len(user.houses) == 3
    for house in houses:
        assert house.owner == user
        assert house.owner_id == user.id 