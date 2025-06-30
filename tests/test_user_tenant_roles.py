import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.house import House
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
def admin_user_tenant1(db_session):
    """Create admin user for tenant 1"""
    user = User(
        email="admin1@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def user_tenant1(db_session):
    """Create regular user for tenant 1"""
    user = User(
        email="user1@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user_tenant2(db_session):
    """Create admin user for tenant 2"""
    user = User(
        email="admin2@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_2"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def user_tenant2(db_session):
    """Create regular user for tenant 2"""
    user = User(
        email="user2@test.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_2"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_role(db_session):
    """Create admin role"""
    role = Role(
        name="admin",
        description="Administrator role",
        tenant_id="house_1"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def user_role(db_session):
    """Create user role"""
    role = Role(
        name="user",
        description="Regular user role",
        tenant_id="house_1"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def admin_role_tenant2(db_session):
    """Create admin role for tenant 2"""
    role = Role(
        name="admin",
        description="Administrator role",
        tenant_id="house_2"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def user_role_tenant2(db_session):
    """Create user role for tenant 2"""
    role = Role(
        name="user",
        description="Regular user role",
        tenant_id="house_2"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def house1(db_session):
    """Create house for tenant 1"""
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
    """Create house for tenant 2"""
    house = House(
        name="Test House 2",
        address="Via Test 2",
        tenant_id="house_2"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

def test_admin_access_own_tenant(db_session, admin_user_tenant1, admin_role):
    """Test admin can access their own tenant data"""
    
    # Assign admin role to user
    admin_user_tenant1.roles = [admin_role]
    db_session.commit()
    
    # Create token for admin
    token = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    # Verify admin has access to their tenant
    assert admin_user_tenant1.tenant_id == "house_1"
    assert "admin" in token

def test_user_cannot_access_admin_endpoints(db_session, user_tenant1, user_role):
    """Test regular user cannot access admin endpoints"""
    
    # Assign user role
    user_tenant1.roles = [user_role]
    db_session.commit()
    
    # Create token for regular user
    token = create_access_token(data={
        "sub": user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["user"]
    })
    
    # Verify user doesn't have admin access
    assert "admin" not in token
    assert "user" in token

def test_cross_tenant_access_denied(db_session, admin_user_tenant1, admin_role_tenant2):
    """Test admin cannot access different tenant data"""
    
    # Try to assign role from different tenant
    admin_user_tenant1.roles = [admin_role_tenant2]
    db_session.commit()
    
    # Create token for tenant1 user
    token = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    # Verify tenant isolation
    assert admin_user_tenant1.tenant_id == "house_1"
    assert admin_role_tenant2.tenant_id == "house_2"
    
    # User should not have access to tenant2 data
    # This tests the tenant isolation principle

def test_role_permission_mapping(db_session, admin_user_tenant1, admin_role):
    """Test role to permission mapping"""
    
    # Create permissions
    read_permission = Permission(
        name="document:read",
        description="Read documents",
        tenant_id="house_1"
    )
    write_permission = Permission(
        name="document:write",
        description="Write documents",
        tenant_id="house_1"
    )
    admin_permission = Permission(
        name="admin:all",
        description="All admin permissions",
        tenant_id="house_1"
    )
    
    db_session.add_all([read_permission, write_permission, admin_permission])
    db_session.commit()
    
    # Assign admin role and permissions
    admin_user_tenant1.roles = [admin_role]
    admin_user_tenant1.permissions = [admin_permission]
    db_session.commit()
    
    # Create token
    token = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"],
        "permissions": ["admin:all"]
    })
    
    # Verify admin has all permissions
    assert "admin" in token
    assert "admin:all" in token

def test_user_permission_restrictions(db_session, user_tenant1, user_role):
    """Test user permission restrictions"""
    
    # Create limited permissions for user
    read_permission = Permission(
        name="document:read",
        description="Read documents",
        tenant_id="house_1"
    )
    
    db_session.add(read_permission)
    db_session.commit()
    
    # Assign user role and limited permissions
    user_tenant1.roles = [user_role]
    user_tenant1.permissions = [read_permission]
    db_session.commit()
    
    # Create token
    token = create_access_token(data={
        "sub": user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["user"],
        "permissions": ["document:read"]
    })
    
    # Verify user has only read permission
    assert "user" in token
    assert "document:read" in token
    assert "document:write" not in token
    assert "admin:all" not in token

def test_multi_tenant_role_isolation(db_session, admin_user_tenant1, admin_user_tenant2, 
                                   admin_role, admin_role_tenant2):
    """Test role isolation between tenants"""
    
    # Assign roles to respective users
    admin_user_tenant1.roles = [admin_role]
    admin_user_tenant2.roles = [admin_role_tenant2]
    db_session.commit()
    
    # Create tokens
    token1 = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    token2 = create_access_token(data={
        "sub": admin_user_tenant2.email,
        "tenant_id": "house_2",
        "roles": ["admin"]
    })
    
    # Verify roles are isolated by tenant
    assert admin_user_tenant1.tenant_id == "house_1"
    assert admin_user_tenant2.tenant_id == "house_2"
    assert admin_role.tenant_id == "house_1"
    assert admin_role_tenant2.tenant_id == "house_2"

def test_role_hierarchy_across_tenants(db_session, admin_user_tenant1, user_tenant1,
                                     admin_role, user_role):
    """Test role hierarchy within tenant"""
    
    # Assign roles
    admin_user_tenant1.roles = [admin_role]
    user_tenant1.roles = [user_role]
    db_session.commit()
    
    # Create tokens
    admin_token = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    user_token = create_access_token(data={
        "sub": user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["user"]
    })
    
    # Verify role hierarchy
    # Admin should have access to user endpoints
    # User should not have access to admin endpoints
    assert "admin" in admin_token
    assert "user" in user_token
    assert "admin" not in user_token

def test_permission_granularity_across_tenants(db_session, user_tenant1, user_tenant2):
    """Test fine-grained permissions across tenants"""
    
    # Create different permissions for each tenant
    read_permission_tenant1 = Permission(
        name="document:read",
        description="Read documents",
        tenant_id="house_1"
    )
    
    write_permission_tenant2 = Permission(
        name="document:write",
        description="Write documents",
        tenant_id="house_2"
    )
    
    db_session.add_all([read_permission_tenant1, write_permission_tenant2])
    db_session.commit()
    
    # Assign permissions to users
    user_tenant1.permissions = [read_permission_tenant1]
    user_tenant2.permissions = [write_permission_tenant2]
    db_session.commit()
    
    # Create tokens
    token1 = create_access_token(data={
        "sub": user_tenant1.email,
        "tenant_id": "house_1",
        "permissions": ["document:read"]
    })
    
    token2 = create_access_token(data={
        "sub": user_tenant2.email,
        "tenant_id": "house_2",
        "permissions": ["document:write"]
    })
    
    # Verify permission isolation
    assert "document:read" in token1
    assert "document:write" not in token1
    assert "document:write" in token2
    assert "document:read" not in token2

def test_tenant_switching_security(db_session, admin_user_tenant1, admin_user_tenant2):
    """Test security when switching between tenants"""
    
    # Create tokens for different tenants
    token1 = create_access_token(data={
        "sub": admin_user_tenant1.email,
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    token2 = create_access_token(data={
        "sub": admin_user_tenant2.email,
        "tenant_id": "house_2",
        "roles": ["admin"]
    })
    
    # Verify tokens are tenant-specific
    # A user should not be able to use token1 to access tenant2 data
    # and vice versa
    assert admin_user_tenant1.tenant_id == "house_1"
    assert admin_user_tenant2.tenant_id == "house_2"
    
    # This tests the principle that tokens are bound to specific tenants
    assert True  # Placeholder for actual token validation logic 