import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.house import House
from app.models.user_house import UserHouse
from app.database import get_db
import json
import uuid

# UUID validi per i test
TENANT_1_UUID = "b3b2c1d0-1234-5678-9abc-def012345678"

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
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
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        tenant_id=test_user.tenant_id,
        role_in_house="resident"
    )
    
    user_house3 = UserHouse(
        user_id=test_user.id,
        house_id=house3.id,
        tenant_id=test_user.tenant_id,
        role_in_house="guest"
    )
    
    db_session.add_all([user_house1, user_house2, user_house3])
    db_session.commit()
    
    # Query user's houses
    user_houses = db_session.query(UserHouse).filter(UserHouse.user_id == test_user.id).all()
    
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
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    resident_relationship = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        tenant_id=test_user.tenant_id,
        role_in_house="resident"
    )
    
    db_session.add_all([owner_relationship, resident_relationship])
    db_session.commit()
    
    # Query relationships
    owner_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    resident_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house2.id
    ).first()
    
    # Verify roles
    assert owner_rel.role_in_house == "owner"
    assert resident_rel.role_in_house == "resident"

def test_house_access_control(db_session, test_user, house1, house2):
    """Test house access control based on user-house relationships"""
    
    # User has access to house1 but not house2
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    db_session.add(user_house1)
    db_session.commit()
    
    # Query accessible houses for user
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    # Verify user can only access house1
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id
    assert accessible_houses[0].name == "Test House 1"

def test_multiple_users_same_house(db_session, house1):
    """Test multiple users can access the same house"""
    
    # Create multiple users
    user1 = User(
        email="user1@test.com",
        username="user1",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    
    user2 = User(
        email="user2@test.com",
        username="user2",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=TENANT_1_UUID
    )
    
    user3 = User(
        email="user3@test.com",
        username="user3",
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
        tenant_id=user1.tenant_id,
        role_in_house="owner"
    )
    
    user2_house = UserHouse(
        user_id=user2.id,
        house_id=house1.id,
        tenant_id=user1.tenant_id,
        role_in_house="resident"
    )
    
    user3_house = UserHouse(
        user_id=user3.id,
        house_id=house1.id,
        tenant_id=user1.tenant_id,
        role_in_house="guest"
    )
    
    db_session.add_all([user1_house, user2_house, user3_house])
    db_session.commit()
    
    # Query users with access to house1
    house_users = db_session.query(User).join(UserHouse).filter(
        UserHouse.house_id == house1.id
    ).all()
    
    # Verify all three users have access
    assert len(house_users) == 3
    
    user_emails = [user.email for user in house_users]
    assert "user1@test.com" in user_emails
    assert "user2@test.com" in user_emails
    assert "user3@test.com" in user_emails

def test_user_house_permissions(db_session, test_user, house1, house2):
    """Test different permissions based on user-house roles"""
    
    # Create relationships with different roles
    owner_relationship = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
        role_in_house="owner",
        permissions='["read", "write", "admin"]'
    )
    
    guest_relationship = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        tenant_id=test_user.tenant_id,
        role_in_house="guest",
        permissions='["read"]'
    )
    
    db_session.add_all([owner_relationship, guest_relationship])
    db_session.commit()
    
    # Query relationships
    owner_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    guest_rel = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house2.id
    ).first()
    
    # Verify different permissions based on roles
    # Owner should have full access, guest should have limited access
    assert owner_rel.role_in_house == "owner"
    assert guest_rel.role_in_house == "guest"
    assert owner_rel.house_id == house1.id
    assert guest_rel.house_id == house2.id
    assert owner_rel.permissions == '["read", "write", "admin"]'
    assert guest_rel.permissions == '["read"]'

def test_house_switching(db_session, test_user, house1, house2):
    """Test user can switch between houses"""
    
    # Create relationships
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        tenant_id=test_user.tenant_id,
        role_in_house="resident"
    )
    
    db_session.add_all([user_house1, user_house2])
    db_session.commit()
    
    # Query all houses user has access to
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    # Verify user can access both houses
    assert len(accessible_houses) == 2
    
    house_ids = [house.id for house in accessible_houses]
    assert house1.id in house_ids
    assert house2.id in house_ids

def test_house_removal(db_session, test_user, house1, house2):
    """Test removing user access to a house"""
    
    # Create relationships
    user_house1 = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    user_house2 = UserHouse(
        user_id=test_user.id,
        house_id=house2.id,
        tenant_id=test_user.tenant_id,
        role_in_house="resident"
    )
    
    db_session.add_all([user_house1, user_house2])
    db_session.commit()
    
    # Remove access to house2
    db_session.delete(user_house2)
    db_session.commit()
    
    # Query remaining accessible houses
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    # Verify user only has access to house1
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id

def test_house_role_upgrade(db_session, test_user, house1):
    """Test upgrading user role in a house"""
    
    # Create initial relationship as guest
    user_house = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
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
    updated_relationship = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    assert updated_relationship.role_in_house == "resident"

def test_house_access_validation(db_session, test_user, house1):
    """Test validation of house access"""
    
    # Create relationship
    user_house = UserHouse(
        user_id=test_user.id,
        house_id=house1.id,
        tenant_id=test_user.tenant_id,
        role_in_house="owner"
    )
    
    db_session.add(user_house)
    db_session.commit()
    
    # Verify relationship exists
    relationship = db_session.query(UserHouse).filter(
        UserHouse.user_id == test_user.id,
        UserHouse.house_id == house1.id
    ).first()
    
    assert relationship is not None
    assert relationship.role_in_house == "owner"
    
    # Verify user can access the house
    accessible_houses = db_session.query(House).join(UserHouse).filter(
        UserHouse.user_id == test_user.id
    ).all()
    
    assert len(accessible_houses) == 1
    assert accessible_houses[0].id == house1.id 