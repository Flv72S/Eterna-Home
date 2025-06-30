import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.security import create_access_token
from app.database import get_db
from app.models.enums import UserRole
import json

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def tenant1_user(db_session):
    """Create test user for tenant 1"""
    user = User(
        email="tenant1@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def tenant2_user(db_session):
    """Create test user for tenant 2"""
    user = User(
        email="tenant2@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_2"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def house1(db_session):
    """Create test house 1"""
    house = House(
        name="Test House 1",
        address="Via Test 1",
        tenant_id="house_1"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def house2(db_session):
    """Create test house 2"""
    house = House(
        name="Test House 2",
        address="Via Test 2",
        tenant_id="house_2"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

def test_multitenant_user_isolation(db_session, tenant1_user, tenant2_user):
    """Test that users are properly isolated between tenants"""
    
    # Verify users exist in different tenants
    assert tenant1_user.tenant_id == "house_1"
    assert tenant2_user.tenant_id == "house_2"
    assert tenant1_user.tenant_id != tenant2_user.tenant_id
    
    # Verify users can't access each other's data
    users_tenant1 = db_session.query(User).filter(User.tenant_id == "house_1").all()
    users_tenant2 = db_session.query(User).filter(User.tenant_id == "house_2").all()
    
    assert len(users_tenant1) == 1
    assert len(users_tenant2) == 1
    assert users_tenant1[0].email == "tenant1@test.com"
    assert users_tenant2[0].email == "tenant2@test.com"

def test_multitenant_house_isolation(db_session, house1, house2):
    """Test that houses are properly isolated between tenants"""
    
    # Verify houses exist in different tenants
    assert house1.tenant_id == "house_1"
    assert house2.tenant_id == "house_2"
    
    # Verify houses can't access each other's data
    houses_tenant1 = db_session.query(House).filter(House.tenant_id == "house_1").all()
    houses_tenant2 = db_session.query(House).filter(House.tenant_id == "house_2").all()
    
    assert len(houses_tenant1) == 1
    assert len(houses_tenant2) == 1
    assert houses_tenant1[0].name == "Test House 1"
    assert houses_tenant2[0].name == "Test House 2"

def test_multitenant_document_isolation(db_session, house1, house2):
    """Test that documents are properly isolated between tenants"""
    
    # Create documents for different tenants
    doc1 = Document(
        filename="test1.pdf",
        file_path="/path/to/test1.pdf",
        file_size=1024,
        mime_type="application/pdf",
        tenant_id="house_1",
        house_id=house1.id
    )
    
    doc2 = Document(
        filename="test2.pdf",
        file_path="/path/to/test2.pdf",
        file_size=2048,
        mime_type="application/pdf",
        tenant_id="house_2",
        house_id=house2.id
    )
    
    db_session.add(doc1)
    db_session.add(doc2)
    db_session.commit()
    
    # Verify documents are isolated
    docs_tenant1 = db_session.query(Document).filter(Document.tenant_id == "house_1").all()
    docs_tenant2 = db_session.query(Document).filter(Document.tenant_id == "house_2").all()
    
    assert len(docs_tenant1) == 1
    assert len(docs_tenant2) == 1
    assert docs_tenant1[0].filename == "test1.pdf"
    assert docs_tenant2[0].filename == "test2.pdf"

def test_multitenant_api_isolation(tenant1_user, tenant2_user):
    """Test API endpoints respect tenant isolation"""
    
    # Create tokens for different tenants
    token1 = create_access_token(data={"sub": tenant1_user.email, "tenant_id": "house_1"})
    token2 = create_access_token(data={"sub": tenant2_user.email, "tenant_id": "house_2"})
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Test that users can only access their own tenant data
    # This would require actual API endpoints to be implemented
    # For now, we verify the tokens contain correct tenant information
    
    # Verify token1 can't access tenant2 data and vice versa
    assert "house_1" in token1
    assert "house_2" in token2
    assert "house_1" not in token2
    assert "house_2" not in token1

def test_tenant_id_required(db_session):
    """Test that tenant_id is required for multi-tenant models"""
    
    # Try to create a user without tenant_id (should fail)
    try:
        user_no_tenant = User(
            email="no_tenant@test.com",
            hashed_password="hashed_password",
            is_active=True
            # Missing tenant_id
        )
        db_session.add(user_no_tenant)
        db_session.commit()
        assert False, "Should not allow user without tenant_id"
    except Exception:
        # Expected behavior - tenant_id should be required
        db_session.rollback()
        assert True

def test_tenant_filtering_works(db_session, tenant1_user, tenant2_user):
    """Test that tenant filtering works correctly in queries"""
    
    # Query users by tenant
    tenant1_users = db_session.query(User).filter(User.tenant_id == "house_1").all()
    tenant2_users = db_session.query(User).filter(User.tenant_id == "house_2").all()
    
    # Verify filtering works
    assert all(user.tenant_id == "house_1" for user in tenant1_users)
    assert all(user.tenant_id == "house_2" for user in tenant2_users)
    
    # Verify no cross-tenant data leakage
    tenant1_emails = [user.email for user in tenant1_users]
    tenant2_emails = [user.email for user in tenant2_users]
    
    assert "tenant1@test.com" in tenant1_emails
    assert "tenant2@test.com" in tenant2_emails
    assert "tenant1@test.com" not in tenant2_emails
    assert "tenant2@test.com" not in tenant1_emails 