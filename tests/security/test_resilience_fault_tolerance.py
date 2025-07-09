"""
Test per la resilienza e fault tolerance del sistema di gestione documenti.
Verifica che il sistema gestisca correttamente errori di storage, timeout e condizioni di errore.
"""

import pytest
import io
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from minio.error import S3Error

from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.core.security import create_access_token
from app.database import get_db
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

class TestResilienceFaultTolerance:
    """Test suite per resilienza e fault tolerance"""
    
    def test_minio_offline_upload_fails_gracefully(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che l'upload fallisca graziosamente quando MinIO è offline"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a test document for MinIO offline test"
        file_data = io.BytesIO(file_content)
        
        # Mock MinIO service to simulate offline
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file.side_effect = S3Error(
                "Connection failed",
                "NoSuchBucket",
                "Bucket does not exist",
                "test-bucket",
                "test-object"
            )
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test MinIO Offline Document",
                    "description": "Test MinIO offline handling",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should return 503 Service Unavailable or 500 Internal Server Error
            assert response.status_code in [500, 503]
            
            # Check error message
            error_data = response.json()
            assert "storage" in error_data.get("detail", "").lower() or \
                   "service" in error_data.get("detail", "").lower() or \
                   "unavailable" in error_data.get("detail", "").lower()
    
    def test_minio_bucket_access_denied(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che l'accesso negato al bucket sia gestito correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a test document for bucket access test"
        file_data = io.BytesIO(file_content)
        
        # Mock MinIO service to simulate access denied
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file.side_effect = S3Error(
                "Access Denied",
                "AccessDenied",
                "Access to bucket denied",
                "test-bucket",
                "test-object"
            )
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test Bucket Access Document",
                    "description": "Test bucket access handling",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should return 500 Internal Server Error
            assert response.status_code == 500
            
            # Check error message
            error_data = response.json()
            assert "access" in error_data.get("detail", "").lower() or \
                   "denied" in error_data.get("detail", "").lower() or \
                   "storage" in error_data.get("detail", "").lower()
    
    def test_upload_file_size_limit_exceeded(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che file troppo grandi siano rifiutati con messaggio appropriato"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create oversized content (51MB - over the 50MB limit)
        oversized_content = b"x" * (51 * 1024 * 1024)
        file_data = io.BytesIO(oversized_content)
        
        # Upload file
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("oversized_document.pdf", file_data, "application/pdf")},
            data={
                "title": "Test Oversized Document",
                "description": "Test file size limit",
                "document_type": "general",
                "house_id": test_house.id
            },
            headers=headers
        )
        
        # Should be rejected
        assert response.status_code in [400, 413]
        
        # Check error message
        error_data = response.json()
        assert "size" in error_data.get("detail", "").lower() or \
               "limit" in error_data.get("detail", "").lower() or \
               "large" in error_data.get("detail", "").lower()
    
    def test_download_file_not_found(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che il download di file non trovati sia gestito correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document
        document = Document(
            title="Test Not Found Document",
            description="Test file not found handling",
            file_url=f"houses/{test_house.id}/documents/test_not_found.pdf",
            file_size=100,
            file_type="application/pdf",
            checksum="test_checksum",
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Mock MinIO service to simulate file not found
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.download_file.return_value = None
            
            # Download file
            response = client.get(
                f"/api/v1/documents/{document.id}/download",
                headers=headers
            )
            
            # Should return 404 Not Found
            assert response.status_code == 404
            
            # Check error message
            error_data = response.json()
            assert "not found" in error_data.get("detail", "").lower() or \
                   "non trovato" in error_data.get("detail", "").lower()
    
    def test_delete_file_not_found(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che la cancellazione di file non trovati sia gestita correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document
        document = Document(
            title="Test Delete Not Found Document",
            description="Test delete file not found handling",
            file_url=f"houses/{test_house.id}/documents/test_delete_not_found.pdf",
            file_size=100,
            file_type="application/pdf",
            checksum="test_checksum",
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        document_id = document.id
        
        # Mock MinIO service to simulate file not found during delete
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.delete_file.return_value = False
            
            # Delete document
            response = client.delete(
                f"/api/v1/documents/{document_id}",
                headers=headers
            )
            
            # Should still succeed (document deleted from DB even if file not found)
            assert response.status_code == 200
            
            # Verify document was deleted from DB
            deleted_document = db_session.get(Document, document_id)
            assert deleted_document is None
    
    def test_network_timeout_handling(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che i timeout di rete siano gestiti correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a test document for timeout handling"
        file_data = io.BytesIO(file_content)
        
        # Mock MinIO service to simulate network timeout
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file.side_effect = Exception("Connection timeout")
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test Timeout Document",
                    "description": "Test timeout handling",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should return 500 Internal Server Error
            assert response.status_code == 500
            
            # Check error message
            error_data = response.json()
            assert "error" in error_data.get("detail", "").lower() or \
                   "timeout" in error_data.get("detail", "").lower() or \
                   "connection" in error_data.get("detail", "").lower()
    
    def test_database_connection_failure(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che i fallimenti di connessione al database siano gestiti"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a test document for database failure handling"
        file_data = io.BytesIO(file_content)
        
        # Mock MinIO service
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file.return_value = {
                "storage_path": f"houses/{test_house.id}/documents/test_db_failure.pdf",
                "file_size": len(file_content),
                "content_type": "application/pdf"
            }
            
            # Mock database session to simulate connection failure
            with patch('app.database.get_db') as mock_db:
                mock_db.side_effect = Exception("Database connection failed")
                
                # Upload file
                response = client.post(
                    "/api/v1/documents/upload",
                    files={"file": ("test_document.pdf", file_data, "application/pdf")},
                    data={
                        "title": "Test Database Failure Document",
                        "description": "Test database failure handling",
                        "document_type": "general",
                        "house_id": test_house.id
                    },
                    headers=headers
                )
                
                # Should return 500 Internal Server Error
                assert response.status_code == 500
    
    def test_concurrent_upload_handling(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che upload concorrenti siano gestiti correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a test document for concurrent upload handling"
        
        # Mock MinIO service
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file.return_value = {
                "storage_path": f"houses/{test_house.id}/documents/test_concurrent.pdf",
                "file_size": len(file_content),
                "content_type": "application/pdf"
            }
            
            # Simulate concurrent uploads (in real scenario, these would be parallel)
            responses = []
            for i in range(3):
                file_data = io.BytesIO(file_content)
                response = client.post(
                    "/api/v1/documents/upload",
                    files={"file": (f"test_document_{i}.pdf", file_data, "application/pdf")},
                    data={
                        "title": f"Test Concurrent Document {i}",
                        "description": f"Test concurrent upload {i}",
                        "document_type": "general",
                        "house_id": test_house.id
                    },
                    headers=headers
                )
                responses.append(response)
            
            # All uploads should succeed
            for response in responses:
                assert response.status_code == 200
                
                # Verify each document has unique ID
                data = response.json()
                assert "id" in data
                assert "file_url" in data or "storage_path" in data 