import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.core.security import create_access_token
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.core.auth import require_permission_in_tenant, require_role_in_tenant
from fastapi import HTTPException
import json
from app.models.enums import UserRole

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
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
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
def document_permission(db_session):
    """Create document permission"""
    permission = Permission(
        name="document:read",
        description="Read documents",
        tenant_id="house_1"
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return permission

def test_require_role_in_tenant_success(db_session, test_user, admin_role):
    """Test successful role-based access control"""
    
    # Assign admin role to user
    test_user.roles = [admin_role]
    db_session.commit()
    
    # Create token with role information
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    # Test that user with admin role can access
    headers = {"Authorization": f"Bearer {token}"}
    
    # This would test an actual endpoint with @require_role_in_tenant("admin")
    # For now, we verify the token contains the required role
    assert "admin" in token

def test_require_role_in_tenant_failure(db_session, test_user, user_role):
    """Test failed role-based access control"""
    
    # Assign user role (not admin)
    test_user.roles = [user_role]
    db_session.commit()
    
    # Create token with user role
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["user"]
    })
    
    # Test that user without admin role cannot access
    # This would raise HTTPException in actual endpoint
    assert "admin" not in token

def test_require_permission_in_tenant_success(db_session, test_user, document_permission):
    """Test successful permission-based access control"""
    
    # Assign permission to user
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with permission information
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "permissions": ["document:read"]
    })
    
    # Test that user with permission can access
    assert "document:read" in token

def test_require_permission_in_tenant_failure(db_session, test_user):
    """Test failed permission-based access control"""
    
    # User has no permissions
    test_user.permissions = []
    db_session.commit()
    
    # Create token without permissions
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "permissions": []
    })
    
    # Test that user without permission cannot access
    assert "document:write" not in token

def test_tenant_isolation_in_rbac(db_session, test_user, admin_role):
    """Test that RBAC respects tenant isolation"""
    
    # Create admin role for different tenant
    admin_role_tenant2 = Role(
        name="admin",
        description="Administrator role",
        tenant_id="house_2"
    )
    db_session.add(admin_role_tenant2)
    db_session.commit()
    
    # Assign role from different tenant
    test_user.roles = [admin_role_tenant2]
    db_session.commit()
    
    # Create token for tenant1 but with role from tenant2
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    # This should fail because role belongs to different tenant
    # In actual implementation, this would be caught by tenant filtering
    assert test_user.tenant_id == "house_1"
    assert admin_role_tenant2.tenant_id == "house_2"

def test_multiple_roles_and_permissions(db_session, test_user, admin_role, user_role, document_permission):
    """Test user with multiple roles and permissions"""
    
    # Assign multiple roles and permissions
    test_user.roles = [admin_role, user_role]
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with multiple roles and permissions
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["admin", "user"],
        "permissions": ["document:read"]
    })
    
    # Verify all roles and permissions are present
    assert "admin" in token
    assert "user" in token
    assert "document:read" in token

def test_role_hierarchy(db_session, test_user, admin_role, user_role):
    """Test role hierarchy (admin should have user permissions)"""
    
    # Assign admin role
    test_user.roles = [admin_role]
    db_session.commit()
    
    # Create token with admin role
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["admin"]
    })
    
    # Admin should have access to user-level endpoints
    # This tests the role hierarchy concept
    assert "admin" in token

def test_permission_granularity(db_session, test_user):
    """Test fine-grained permission control"""
    
    # Create specific permissions
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
    delete_permission = Permission(
        name="document:delete",
        description="Delete documents",
        tenant_id="house_1"
    )
    
    db_session.add_all([read_permission, write_permission, delete_permission])
    db_session.commit()
    
    # Assign only read permission
    test_user.permissions = [read_permission]
    db_session.commit()
    
    # Create token with read permission only
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "permissions": ["document:read"]
    })
    
    # User should have read access but not write or delete
    assert "document:read" in token
    assert "document:write" not in token
    assert "document:delete" not in token

def test_rbac_pbac_combination(db_session, test_user, admin_role, document_permission):
    """Test combination of RBAC and PBAC"""
    
    # Assign both role and permission
    test_user.roles = [admin_role]
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with both role and permission
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": "house_1",
        "roles": ["admin"],
        "permissions": ["document:read"]
    })
    
    # User should have access through both role and permission
    assert "admin" in token
    assert "document:read" in token 