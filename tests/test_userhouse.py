import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from sqlalchemy import text
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.house import House
from app.models.user_house import UserHouse
from app.database import get_db
import json
import uuid

# UUID validi per i test
TENANT_1_UUID = uuid.UUID("b3b2c1d0-1234-5678-9abc-def012345678")

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture(autouse=True)
def clean_db(db_session):
    """Clean database before each test"""
    db_session.execute(text('DELETE FROM user_houses'))
    db_session.execute(text('DELETE FROM houses'))
    db_session.execute(text('DELETE FROM users'))
    db_session.commit()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test_userhouse@example.com", 
        username="testuserhouse",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def house1(db_session, test_user):
    """Create first test house"""
    house = House(
        name="Test House 1",
        address="Via Test 1", 
        owner_id=test_user.id,
        tenant_id=TENANT_1_UUID
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def house2(db_session, test_user):
    """Create second test house"""
    house = House(
        name="Test House 2",
        address="Via Test 2", 
        owner_id=test_user.id,
        tenant_id=TENANT_1_UUID
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def house3(db_session, test_user):
    """Create third test house"""
    house = House(
        name="Test House 3",
        address="Via Test 3", 
        owner_id=test_user.id,
        tenant_id=TENANT_1_UUID
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

def test_user_can_access_multiple_houses(db_session, test_user, house1, house2, house3):
    """Test that a user can be associated with multiple houses"""
    
    # Create user-house relationships
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        role_in_house="resident"
    )
    
    user_house3 = UserHouse(
        user_id=test_user.id,
        house_id=house3.id,
        role_in_house="guest"
    )
    
    db_session.add_all([user_house1, user_house2, user_house3])
    db_session.commit()
    
    # Query user's houses
    user_houses = db_session.exec(select(UserHouse).where(UserHouse.user_id == test_user.id)).all()
    
    # Verify user has access to all three houses
    assert len(user_houses) == 3
    
    # Verify different roles
    roles = [uh.role_in_house for uh in user_houses]
    assert "owner" in roles
    assert "resident" in roles
    assert "guest" in roles

def test_user_house_roles(db_session, test_user, house1, house2):
    """Test different user roles in houses"""
    
    # Create user-house relationships with different roles
    owner_relationship = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    resident_relationship = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        role_in_house="resident"
    )
    
    db_session.add_all([owner_relationship, resident_relationship])
    db_session.commit()
    
    # Query relationships
    owner_rel = db_session.exec(select(UserHouse).where(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    )).first()
    
    resident_rel = db_session.exec(select(UserHouse).where(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house2.id
    )).first()
    
    # Verify roles
    assert owner_rel.role_in_house == "owner"
    assert resident_rel.role_in_house == "resident"

def test_house_access_control(db_session, test_user, house1, house2):
    """Test house access control based on user-house relationships"""
    
    # User has access to house1 but not house2
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    db_session.add(user_house1)
    db_session.commit()
    
    # Query accessible houses for user
    accessible_houses = db_session.exec(select(House).join(UserHouse).where(
        UserHouse.user_id == test_user.id
    )).all()
    
    # Verify user can only access house1
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id
    assert accessible_houses[0].name == "Test House 1"

def test_multiple_users_same_house(db_session, house1):
    """Test multiple users can access the same house"""
    
    # Create multiple users with unique emails
    user1 = User(
        email="user1_house@test.com", 
        username="user1_house",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    
    user2 = User(
        email="user2_house@test.com", 
        username="user2_house",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    
    user3 = User(
        email="user3_house@test.com", 
        username="user3_house",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    
    # Create user-house relationships
    user1_house = UserHouse(
        user_id=user1.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    user2_house = UserHouse(
        user_id=user2.id,
        house_id=house1.id,
        role_in_house="resident"
    )
    
    user3_house = UserHouse(
        user_id=user3.id,
        house_id=house1.id,
        role_in_house="guest"
    )
    
    db_session.add_all([user1_house, user2_house, user3_house])
    db_session.commit()
    
    # Query all users for the house
    house_users = db_session.query(UserHouse).filter(UserHouse.house_id == house1.id).all()
    
    # Verify three users have access to the house
    assert len(house_users) == 3
    
    # Verify different roles
    roles = [uh.role_in_house for uh in house_users]
    assert "owner" in roles
    assert "resident" in roles
    assert "guest" in roles

def test_user_house_permissions(db_session, test_user, house1, house2):
    """Test user permissions in different houses"""
    
    # Create user-house relationships with different permissions
    owner_permissions = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner",
        permissions='{"read": true, "write": true, "delete": true}'
    )
    
    guest_permissions = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        role_in_house="guest",
        permissions='{"read": true, "write": false, "delete": false}'
    )
    
    db_session.add_all([owner_permissions, guest_permissions])
    db_session.commit()
    
    # Query permissions
    owner_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    guest_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house2.id
    ).first()
    
    # Verify permissions
    assert owner_rel.permissions == '{"read": true, "write": true, "delete": true}'
    assert guest_rel.permissions == '{"read": true, "write": false, "delete": false}'

def test_house_switching(db_session, test_user, house1, house2):
    """Test user can switch between houses"""
    
    # Initially user has access to house1
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    db_session.add(user_house1)
    db_session.commit()
    
    # Verify user has access to house1
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id
    
    # Add access to house2
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        role_in_house="resident"
    )
    
    db_session.add(user_house2)
    db_session.commit()
    
    # Verify user now has access to both houses
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 2
    house_ids = [h.id for h in accessible_houses]
    assert house1.id in house_ids
    assert house2.id in house_ids

def test_house_removal(db_session, test_user, house1, house2):
    """Test removing user access to a house"""
    
    # User has access to both houses
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        role_in_house="resident"
    )
    
    db_session.add_all([user_house1, user_house2])
    db_session.commit()
    
    # Verify user has access to both houses
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 2
    
    # Remove access to house2
    db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house2.id
    ).delete()
    db_session.commit()
    
    # Verify user now only has access to house1
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id

def test_house_role_upgrade(db_session, test_user, house1):
    """Test upgrading user role in a house"""
    
    # Initially user is a guest
    user_house = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="guest"
    )
    
    db_session.add(user_house)
    db_session.commit()
    
    # Verify initial role
    relationship = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    assert relationship.role_in_house == "guest"
    
    # Upgrade to resident
    relationship.role_in_house = "resident"
    db_session.commit()
    
    # Verify role upgrade
    relationship = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    assert relationship.role_in_house == "resident"

def test_house_access_validation(db_session, test_user, house1):
    """Test validation of house access"""
    
    # User has no access to house initially
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 0
    
    # Add access
    user_house = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        role_in_house="owner"
    )
    
    db_session.add(user_house)
    db_session.commit()
    
    # Verify access is granted
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id 
