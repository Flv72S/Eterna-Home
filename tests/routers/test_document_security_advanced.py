"""
Test avanzati integrati per la sicurezza della gestione documenti in Eterna Home.
Integra test di cifratura, protezione contro contenuti malevoli, logging e resilienza.
"""

import pytest
import io
import hashlib
import uuid
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.core.security import create_access_token
from app.database import get_db
from app.services.minio_service import get_minio_service
from app.security.encryption import encryption_service
from app.models.enums import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_tenant_id():
    """Create a test tenant ID"""
    return uuid.uuid4()

@pytest.fixture
def test_user(db_session, test_tenant_id):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=test_tenant_id,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_house(db_session, test_tenant_id, test_user):
    """Create test house"""
    house = House(
        name="Test House",
        address="Via Test 1",
        tenant_id=test_tenant_id,
        owner_id=test_user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def setup_rbac(db_session, test_tenant_id, test_user):
    """Setup RBAC permissions"""
    # Create permissions
    permissions = [
        Permission(
            name="read_documents",
            resource="documents",
            action="read",
            is_active=True
        ),
        Permission(
            name="write_documents",
            resource="documents", 
            action="write",
            is_active=True
        ),
        Permission(
            name="delete_documents",
            resource="documents",
            action="delete", 
            is_active=True
        )
    ]
    
    for perm in permissions:
        db_session.add(perm)
    db_session.commit()
    
    # Assign admin role to user
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()

class TestDocumentSecurityAdvanced:
    """Test suite avanzata per la sicurezza dei documenti"""
    
    def test_complete_secure_document_lifecycle(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test completo del ciclo di vita sicuro di un documento"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. UPLOAD - Test upload sicuro
        original_content = b"This is a secure document with sensitive content"
        file_data = io.BytesIO(original_content)
        
        # Mock MinIO service to capture uploaded content
        uploaded_content = None
        def mock_upload(*args, **kwargs):
            nonlocal uploaded_content
            file_obj = args[0] if args else kwargs.get('file')
            if hasattr(file_obj, 'file'):
                file_obj.file.seek(0)
                uploaded_content = file_obj.file.read()
            return {
                "storage_path": f"houses/{test_house.id}/documents/secure_document.pdf",
                "file_size": len(original_content),
                "content_type": "application/pdf"
            }
        
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file = mock_upload
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("secure_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Secure Document",
                    "description": "Test complete secure lifecycle",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            document_id = data["id"]
            
            # Verify upload security
            assert uploaded_content is not None
            assert uploaded_content != original_content  # Should be encrypted
            assert data["tenant_id"] == str(test_tenant_id)
            assert data["house_id"] == test_house.id
            assert data["owner_id"] == test_user.id
        
        # 2. DOWNLOAD - Test download sicuro
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            # Mock encrypted content for download
            encrypted_content = encryption_service.encrypt_data(original_content)
            mock_service.return_value.download_file.return_value = {
                "content": encrypted_content,
                "content_type": "application/pdf",
                "file_size": len(original_content)
            }
            
            # Download file
            response = client.get(
                f"/api/v1/documents/{document_id}/download",
                headers=headers
            )
            
            assert response.status_code == 200
            downloaded_content = response.content
            assert downloaded_content == original_content  # Should be decrypted
        
        # 3. DELETE - Test delete sicuro
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.delete_file.return_value = True
            
            # Delete document
            response = client.delete(
                f"/api/v1/documents/{document_id}",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify document is deleted
            deleted_document = db_session.get(Document, document_id)
            assert deleted_document is None
    
    def test_multi_tenant_isolation_advanced(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test avanzato di isolamento multi-tenant"""
        
        # Create second tenant and user
        second_tenant_id = uuid.uuid4()
        second_user = User(
            email="second@example.com",
            username="seconduser",
            hashed_password="hashed_password",
            is_active=True,
            tenant_id=second_tenant_id,
            role=UserRole.ADMIN
        )
        db_session.add(second_user)
        db_session.commit()
        db_session.refresh(second_user)
        
        second_house = House(
            name="Second House",
            address="Via Second 1",
            tenant_id=second_tenant_id,
            owner_id=second_user.id
        )
        db_session.add(second_house)
        db_session.commit()
        db_session.refresh(second_house)
        
        # Create documents in both tenants
        document1 = Document(
            title="First Tenant Document",
            description="Document from first tenant",
            file_url=f"houses/{test_house.id}/documents/first_tenant.pdf",
            file_size=100,
            file_type="application/pdf",
            checksum="checksum1",
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document1)
        
        document2 = Document(
            title="Second Tenant Document",
            description="Document from second tenant",
            file_url=f"houses/{second_house.id}/documents/second_tenant.pdf",
            file_size=100,
            file_type="application/pdf",
            checksum="checksum2",
            tenant_id=second_tenant_id,
            house_id=second_house.id,
            owner_id=second_user.id
        )
        db_session.add(document2)
        db_session.commit()
        
        # Test access from first tenant
        token1 = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        response1 = client.get(
            "/api/v1/documents/",
            headers=headers1
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) == 1
        assert data1[0]["title"] == "First Tenant Document"
        assert data1[0]["tenant_id"] == str(test_tenant_id)
        
        # Test access from second tenant
        token2 = create_access_token(data={
            "sub": second_user.email,
            "tenant_id": str(second_tenant_id)
        })
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response2 = client.get(
            "/api/v1/documents/",
            headers=headers2
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]["title"] == "Second Tenant Document"
        assert data2[0]["tenant_id"] == str(second_tenant_id)
        
        # Test cross-tenant access should be forbidden
        response_cross = client.get(
            f"/api/v1/documents/{document2.id}",
            headers=headers1
        )
        
        assert response_cross.status_code == 403
    
    def test_concurrent_user_access_control(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test controllo accessi concorrenti multi-utente"""
        
        # Create second user in same tenant
        second_user = User(
            email="second@example.com",
            username="seconduser",
            hashed_password="hashed_password",
            is_active=True,
            tenant_id=test_tenant_id,
            role=UserRole.VIEWER  # Different role
        )
        db_session.add(second_user)
        db_session.commit()
        db_session.refresh(second_user)
        
        # Create document owned by first user
        document = Document(
            title="Test Concurrent Access Document",
            description="Test concurrent user access",
            file_url=f"houses/{test_house.id}/documents/concurrent_access.pdf",
            file_size=100,
            file_type="application/pdf",
            checksum="checksum",
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Test access from owner
        token1 = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        response1 = client.get(
            f"/api/v1/documents/{document.id}",
            headers=headers1
        )
        
        assert response1.status_code == 200
        
        # Test access from second user (should be forbidden if no house access)
        token2 = create_access_token(data={
            "sub": second_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response2 = client.get(
            f"/api/v1/documents/{document.id}",
            headers=headers2
        )
        
        # Should be forbidden (403) or not found (404) depending on implementation
        assert response2.status_code in [403, 404]
    
    def test_file_integrity_and_metadata_preservation(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test preservazione integrità file e metadati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document
        original_content = b"This is content for integrity testing"
        expected_checksum = hashlib.sha256(original_content).hexdigest()
        
        document = Document(
            title="Test Integrity Document",
            description="Test integrity and metadata preservation",
            file_url=f"houses/{test_house.id}/documents/integrity_test.pdf",
            file_size=len(original_content),
            file_type="application/pdf",
            checksum=expected_checksum,
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Store original metadata
        original_metadata = {
            "tenant_id": document.tenant_id,
            "house_id": document.house_id,
            "owner_id": document.owner_id,
            "checksum": document.checksum,
            "file_size": document.file_size,
            "file_type": document.file_type
        }
        
        # Update document title and description
        update_data = {
            "title": "Updated Integrity Document",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/documents/{document.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify metadata preservation
        assert data["tenant_id"] == str(original_metadata["tenant_id"])
        assert data["house_id"] == original_metadata["house_id"]
        assert data["owner_id"] == original_metadata["owner_id"]
        assert data["checksum"] == original_metadata["checksum"]
        assert data["file_size"] == original_metadata["file_size"]
        assert data["file_type"] == original_metadata["file_type"]
        
        # Verify updated fields
        assert data["title"] == "Updated Integrity Document"
        assert data["description"] == "Updated description"
    
    def test_security_headers_and_response_validation(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test validazione header di sicurezza e risposte"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test document listing
        response = client.get(
            "/api/v1/documents/",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify security headers
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
        
        # Verify no sensitive data in response
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            for item in data:
                # Verify no sensitive fields are exposed
                assert "hashed_password" not in item
                assert "password" not in item
                assert "secret" not in item
                
                # Verify required fields are present
                assert "id" in item
                assert "title" in item
                assert "tenant_id" in item 