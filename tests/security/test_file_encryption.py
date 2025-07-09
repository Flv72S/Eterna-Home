"""
Test avanzati per la cifratura dei file in Eterna Home.
Verifica che i file siano effettivamente cifrati su MinIO e che la decrittografia funzioni correttamente.
"""

import pytest
import io
import hashlib
import uuid
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

class TestFileEncryption:
    """Test suite per la cifratura dei file"""
    
    def test_upload_file_encrypted_on_storage(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che il file caricato sia effettivamente cifrato su MinIO"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        original_content = b"This is a test document with sensitive content"
        file_data = io.BytesIO(original_content)
        
        # Mock MinIO service to capture uploaded content
        uploaded_content = None
        
        async def mock_upload(*args, **kwargs):
            nonlocal uploaded_content
            # Capture the content that would be uploaded
            file_obj = args[0] if args else kwargs.get('file')
            if hasattr(file_obj, 'file'):
                file_obj.file.seek(0)
                uploaded_content = file_obj.file.read()
            return {
                "storage_path": f"houses/{test_house.id}/documents/test_encrypted.pdf",
                "file_size": len(original_content),
                "content_type": "application/pdf"
            }
        
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file = mock_upload
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test Encrypted Document",
                    "description": "Test encryption",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify that uploaded content is different from original (encrypted)
            assert uploaded_content is not None
            assert uploaded_content != original_content
            
            # Verify that uploaded content is not readable as plain text
            try:
                uploaded_content.decode('utf-8')
                # If we can decode it, it's not properly encrypted
                assert False, "Uploaded content should not be readable as plain text"
            except UnicodeDecodeError:
                # This is expected - encrypted content should not be UTF-8 decodable
                pass
    
    def test_download_file_decryption(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che il download decifri correttamente il file"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document with encrypted content
        original_content = b"This is the original document content"
        
        # Encrypt the content
        encrypted_content = encryption_service.encrypt_data(original_content)
        
        # Create document record
        document = Document(
            title="Test Encrypted Document",
            description="Test decryption",
            file_url=f"houses/{test_house.id}/documents/test_encrypted.pdf",
            file_size=len(original_content),
            file_type="application/pdf",
            checksum=hashlib.sha256(original_content).hexdigest(),
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Mock MinIO download to return encrypted content
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.download_file.return_value = {
                "content": encrypted_content,
                "content_type": "application/pdf",
                "file_size": len(encrypted_content)
            }
            
            # Download file
            response = client.get(
                f"/api/v1/documents/{document.id}/download",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify downloaded content matches original
            downloaded_content = response.content
            assert downloaded_content == original_content
    
    def test_download_with_wrong_key_fails(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che il download con chiave errata generi errore"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document
        original_content = b"This is the original document content"
        
        # Create document record
        document = Document(
            title="Test Document",
            description="Test wrong key",
            file_url=f"houses/{test_house.id}/documents/test.pdf",
            file_size=len(original_content),
            file_type="application/pdf",
            checksum=hashlib.sha256(original_content).hexdigest(),
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Mock MinIO download to return corrupted encrypted content
        corrupted_content = b"corrupted_encrypted_data"
        
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.download_file.return_value = {
                "content": corrupted_content,
                "content_type": "application/pdf",
                "file_size": len(corrupted_content)
            }
            
            # Download file should fail
            response = client.get(
                f"/api/v1/documents/{document.id}/download",
                headers=headers
            )
            
            # Should return error due to decryption failure
            assert response.status_code in [400, 500]
    
    def test_file_integrity_checksum_verification(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test verifica integrità file tramite checksum"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        original_content = b"This is a test document for integrity check"
        expected_checksum = hashlib.sha256(original_content).hexdigest()
        file_data = io.BytesIO(original_content)
        
        # Mock MinIO service
        async def mock_upload(*args, **kwargs):
            return {
                "storage_path": f"houses/{test_house.id}/documents/test_integrity.pdf",
                "file_size": len(original_content),
                "content_type": "application/pdf"
            }
        
        with patch('app.services.minio_service.get_minio_service') as mock_service:
            mock_service.return_value.upload_file = mock_upload
            
            # Upload file
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test_document.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test Integrity Document",
                    "description": "Test checksum verification",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify checksum is stored correctly
            assert "checksum" in data
            assert data["checksum"] == expected_checksum
    
    def test_encryption_key_rotation_simulation(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test simulazione rotazione chiavi crittografiche"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test document
        original_content = b"This is content that should survive key rotation"
        
        document = Document(
            title="Test Key Rotation",
            description="Test key rotation simulation",
            file_url=f"houses/{test_house.id}/documents/test_rotation.pdf",
            file_size=len(original_content),
            file_type="application/pdf",
            checksum=hashlib.sha256(original_content).hexdigest(),
            tenant_id=test_tenant_id,
            house_id=test_house.id,
            owner_id=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        # Simulate key rotation by re-encrypting with new key
        with patch('app.security.encryption.encryption_service') as mock_encryption:
            # First encryption
            mock_encryption.encrypt_data.return_value = b"encrypted_with_old_key"
            
            # Simulate download with old key
            with patch('app.services.minio_service.get_minio_service') as mock_service:
                mock_service.return_value.download_file.return_value = {
                    "content": b"encrypted_with_old_key",
                    "content_type": "application/pdf",
                    "file_size": len(original_content)
                }
                
                response = client.get(
                    f"/api/v1/documents/{document.id}/download",
                    headers=headers
                )
                
                # Should still work with old key
                assert response.status_code == 200 