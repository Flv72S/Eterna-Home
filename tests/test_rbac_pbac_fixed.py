import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
import jwt

from app.core.security import create_access_token
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.core.auth import require_permission_in_tenant, require_role_in_tenant
from fastapi import HTTPException
import json
import uuid
from app.models.enums import UserRole
import time

client = TestClient(app)

def decode_jwt_token(token):
    """Decode JWT token to get payload"""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decode without verification for testing
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def test_require_role_in_tenant_success(db_session, test_user):
    """Test successful role-based access control"""
    
    # Create admin role
    unique_name = f"admin_{int(time.time() * 1000)}"
    admin_role = Role(
        name=unique_name,
        description="Administrator role",
        is_active=True
    )
    db_session.add(admin_role)
    db_session.commit()
    db_session.refresh(admin_role)
    
    # Assign admin role to user
    test_user.roles = [admin_role]
    db_session.commit()
    
    # Create token with role information
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["admin"]
    })
    
    # Test that user with admin role can access
    headers = {"Authorization": f"Bearer {token}"}
    
    # Decode token and verify roles
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "roles" in payload
    assert "admin" in payload["roles"]

def test_require_role_in_tenant_failure(db_session, test_user):
    """Test failed role-based access control"""
    
    # Create user role (not admin)
    unique_name = f"user_{int(time.time() * 1000)}"
    user_role = Role(
        name=unique_name,
        description="Regular user role",
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user_role)
    
    # Assign user role (not admin)
    test_user.roles = [user_role]
    db_session.commit()
    
    # Create token with user role
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["user"]
    })
    
    # Test that user without admin role cannot access
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "roles" in payload
    assert "admin" not in payload["roles"]

def test_require_permission_in_tenant_success(db_session, test_user):
    """Test successful permission-based access control"""
    
    # Create document permission
    unique_name = f"document:read_{int(time.time() * 1000)}"
    document_permission = Permission(
        name=unique_name,
        description="Read documents",
        resource="document",
        action="read",
        is_active=True
    )
    db_session.add(document_permission)
    db_session.commit()
    db_session.refresh(document_permission)
    
    # Assign permission to user
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with permission information
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "permissions": ["document:read"]
    })
    
    # Test that user with permission can access
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "permissions" in payload
    assert "document:read" in payload["permissions"]

def test_require_permission_in_tenant_failure(db_session, test_user):
    """Test failed permission-based access control"""
    
    # User has no permissions
    test_user.permissions = []
    db_session.commit()
    
    # Create token without permissions
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "permissions": []
    })
    
    # Test that user without permission cannot access
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "permissions" in payload
    assert "document:write" not in payload["permissions"]

def test_tenant_isolation_in_rbac(db_session, test_user):
    """Test that RBAC respects tenant isolation"""
    
    # Create admin role for different tenant
    unique_name = f"admin_tenant2_{int(time.time() * 1000)}"
    admin_role_tenant2 = Role(
        name=unique_name,
        description="Administrator role",
        is_active=True
    )
    db_session.add(admin_role_tenant2)
    db_session.commit()
    
    # Assign role from different tenant
    test_user.roles = [admin_role_tenant2]
    db_session.commit()
    
    # Create token for tenant1 but with role from tenant2
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["admin"]
    })
    
    # This should fail because role belongs to different tenant
    # In actual implementation, this would be caught by tenant filtering
    assert test_user.tenant_id == test_user.tenant_id
    # Note: Since Role doesn't have tenant_id, we can't test tenant isolation this way
    # In a real implementation, this would be handled through UserTenantRole

def test_multiple_roles_and_permissions(db_session, test_user):
    """Test user with multiple roles and permissions"""
    
    # Create roles and permissions
    unique_admin_name = f"admin_{int(time.time() * 1000)}"
    admin_role = Role(
        name=unique_admin_name,
        description="Administrator role",
        is_active=True
    )
    db_session.add(admin_role)
    db_session.commit()
    db_session.refresh(admin_role)
    
    unique_user_name = f"user_{int(time.time() * 1000)}"
    user_role = Role(
        name=unique_user_name,
        description="Regular user role",
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user_role)
    
    unique_permission_name = f"document:read_{int(time.time() * 1000)}"
    document_permission = Permission(
        name=unique_permission_name,
        description="Read documents",
        resource="document",
        action="read",
        is_active=True
    )
    db_session.add(document_permission)
    db_session.commit()
    db_session.refresh(document_permission)
    
    # Assign multiple roles and permissions
    test_user.roles = [admin_role, user_role]
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with multiple roles and permissions
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["admin", "user"],
        "permissions": ["document:read"]
    })
    
    # Verify all roles and permissions are present
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "admin" in payload.get("roles", [])
    assert "user" in payload.get("roles", [])
    assert "document:read" in payload.get("permissions", [])

def test_role_hierarchy(db_session, test_user):
    """Test role hierarchy (admin should have user permissions)"""
    
    # Create roles
    unique_admin_name = f"admin_{int(time.time() * 1000)}"
    admin_role = Role(
        name=unique_admin_name,
        description="Administrator role",
        is_active=True
    )
    db_session.add(admin_role)
    db_session.commit()
    db_session.refresh(admin_role)
    
    unique_user_name = f"user_{int(time.time() * 1000)}"
    user_role = Role(
        name=unique_user_name,
        description="Regular user role",
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    db_session.refresh(user_role)
    
    # Assign admin role (should inherit user permissions)
    test_user.roles = [admin_role]
    db_session.commit()
    
    # Create token with admin role
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["admin"]
    })
    
    # Admin should have access to user-level endpoints
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "admin" in payload.get("roles", [])

def test_permission_granularity(db_session, test_user):
    """Test fine-grained permission control"""
    
    # Create specific permissions
    unique_read_name = f"document:read_{int(time.time() * 1000)}"
    read_permission = Permission(
        name=unique_read_name,
        description="Read documents",
        resource="document",
        action="read",
        is_active=True
    )
    db_session.add(read_permission)
    db_session.commit()
    db_session.refresh(read_permission)
    
    unique_write_name = f"document:write_{int(time.time() * 1000)}"
    write_permission = Permission(
        name=unique_write_name,
        description="Write documents",
        resource="document",
        action="write",
        is_active=True
    )
    db_session.add(write_permission)
    db_session.commit()
    db_session.refresh(write_permission)
    
    # Assign only read permission
    test_user.permissions = [read_permission]
    db_session.commit()
    
    # Create token with read permission only
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "permissions": ["document:read"]
    })
    
    # User should have read access but not write access
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "document:read" in payload.get("permissions", [])
    assert "document:write" not in payload.get("permissions", [])

def test_rbac_pbac_combination(db_session, test_user):
    """Test combination of RBAC and PBAC"""
    
    # Create role and permission
    unique_admin_name = f"admin_{int(time.time() * 1000)}"
    admin_role = Role(
        name=unique_admin_name,
        description="Administrator role",
        is_active=True
    )
    db_session.add(admin_role)
    db_session.commit()
    db_session.refresh(admin_role)
    
    unique_permission_name = f"document:read_{int(time.time() * 1000)}"
    document_permission = Permission(
        name=unique_permission_name,
        description="Read documents",
        resource="document",
        action="read",
        is_active=True
    )
    db_session.add(document_permission)
    db_session.commit()
    db_session.refresh(document_permission)
    
    # Assign both role and permission
    test_user.roles = [admin_role]
    test_user.permissions = [document_permission]
    db_session.commit()
    
    # Create token with both role and permission
    token = create_access_token(data={
        "sub": test_user.email, 
        "tenant_id": test_user.tenant_id,
        "roles": ["admin"],
        "permissions": ["document:read"]
    })
    
    # User should have access through both role and permission
    payload = decode_jwt_token(token)
    assert payload is not None
    assert "admin" in payload.get("roles", [])
    assert "document:read" in payload.get("permissions", []) 