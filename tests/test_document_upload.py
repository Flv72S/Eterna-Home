import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.security import create_access_token
from app.database import get_db
from app.services.minio_service import MinIOService
from app.security.encryption import encrypt_file, decrypt_file
import io
import uuid
import os
from unittest.mock import patch, MagicMock
from sqlmodel import Session
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
def test_house(db_session, test_tenant_id):
    """Create test house"""
    house = House(
        name="Test House",
        address="Via Test 1",
        tenant_id=test_tenant_id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def mock_minio_service():
    """Mock MinIO service"""
    with patch('app.services.minio_service.get_minio_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

def test_document_upload_success(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test successful document upload"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file content
    file_content = b"This is a test document content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload response
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/test_document.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", file_data, "application/pdf")},
        data={
            "title": "Test Document",
            "description": "Test description",
            "document_type": "general",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["file_size"] == len(file_content)
    assert data["file_type"] == "application/pdf"
    assert data["tenant_id"] == str(test_tenant_id)
    assert data["house_id"] == test_house.id

def test_document_upload_with_encryption(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document upload with encryption"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file content
    file_content = b"This is sensitive document content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload with encryption
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/encrypted_document.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("encrypted_document.pdf", file_data, "application/pdf")},
        data={
            "title": "Encrypted Document",
            "description": "Sensitive document",
            "document_type": "confidential",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Encrypted Document"
    assert data["document_type"] == "confidential"

def test_document_path_structure(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test correct document path structure"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    expected_path = f"houses/{test_house.id}/documents/test.pdf"
    mock_minio_service.upload_file.return_value = {
        "storage_path": expected_path,
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={
            "title": "Test Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify path structure
    assert response.status_code == 200
    data = response.json()
    
    # Verify MinIO was called with correct path
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args
    
    # Path should follow pattern: houses/house_id/documents/filename
    assert "houses" in call_args[1]["folder"]
    assert str(test_house.id) in call_args[1]["folder"]
    assert "documents" in call_args[1]["folder"]

def test_document_filename_sanitization(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test filename sanitization"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file with problematic filename
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/sanitized_filename.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file with problematic filename
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("../../../malicious<script>.pdf", file_data, "application/pdf")},
        data={
            "title": "Sanitized Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify MinIO was called with sanitized filename
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args
    
    # Filename should be sanitized
    uploaded_filename = call_args[0][0].filename
    assert "malicious" in uploaded_filename
    assert "<script>" not in uploaded_filename
    assert ".." not in uploaded_filename

def test_document_size_validation(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document size validation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file that's too large (100MB)
    large_content = b"x" * (100 * 1024 * 1024)
    file_data = io.BytesIO(large_content)
    
    # Try to upload large file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large_file.pdf", file_data, "application/pdf")},
        data={
            "title": "Large Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Should fail due to size limit
    assert response.status_code == 413

def test_document_type_validation(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document type validation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file with invalid type
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Try to upload file with invalid type
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.exe", file_data, "application/x-executable")},
        data={
            "title": "Invalid Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Should fail due to invalid file type
    assert response.status_code == 400

def test_document_metadata_storage(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document metadata storage"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/test.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file with metadata
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={
            "title": "Test Document",
            "description": "This is a test document with metadata",
            "document_type": "contract",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["description"] == "This is a test document with metadata"
    assert data["document_type"] == "contract"
    assert data["owner_id"] == test_user.id

def test_document_download(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document download"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document in database
    document = Document(
        title="Test Document",
        file_path=f"houses/{test_house.id}/documents/test.pdf",
        file_size=100,
        file_type="application/pdf",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Mock MinIO download
    mock_minio_service.download_file.return_value = b"Test document content"
    
    # Download document
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.content == b"Test document content"

def test_document_encryption_decryption(test_tenant_id):
    """Test document encryption and decryption"""
    
    # Test content
    original_content = b"This is sensitive content that needs encryption"
    
    # Encrypt content
    encrypted_content = encrypt_file(original_content, test_tenant_id)
    
    # Verify content is encrypted
    assert encrypted_content != original_content
    assert len(encrypted_content) > len(original_content)
    
    # Decrypt content
    decrypted_content = decrypt_file(encrypted_content, test_tenant_id)
    
    # Verify content is correctly decrypted
    assert decrypted_content == original_content

def test_document_tenant_isolation(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document tenant isolation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/test.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={
            "title": "Test Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify MinIO was called with tenant isolation
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args
    
    # Should include tenant_id in the call
    assert call_args[1]["tenant_id"] == test_tenant_id
    assert call_args[1]["house_id"] == test_house.id 