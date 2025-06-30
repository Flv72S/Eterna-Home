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
def test_house(db_session):
    """Create test house"""
    house = House(
        name="Test House",
        address="Via Test 1",
        tenant_id="house_1"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def mock_minio_service():
    """Mock MinIO service"""
    with patch('app.services.minio_service.MinIOService') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

def test_document_upload_success(db_session, test_user, test_house, mock_minio_service):
    """Test successful document upload"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file content
    file_content = b"This is a test document content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload response
    mock_minio_service.upload_file.return_value = {
        "file_path": f"house_1/{test_house.id}/documents/test_document.pdf",
        "file_size": len(file_content),
        "etag": "test-etag"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_document.pdf"
    assert data["file_size"] == len(file_content)
    assert data["mime_type"] == "application/pdf"
    assert data["tenant_id"] == "house_1"
    assert data["house_id"] == test_house.id

def test_document_upload_with_encryption(db_session, test_user, test_house, mock_minio_service):
    """Test document upload with encryption"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file content
    file_content = b"This is sensitive document content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload with encryption
    mock_minio_service.upload_file.return_value = {
        "file_path": f"house_1/{test_house.id}/documents/encrypted_document.pdf",
        "file_size": len(file_content),
        "etag": "test-etag",
        "is_encrypted": True
    }
    
    # Upload file with encryption
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("encrypted_document.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id, "encrypt": "true"},
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["is_encrypted"] == True
    assert data["filename"] == "encrypted_document.pdf"

def test_document_path_structure(db_session, test_user, test_house, mock_minio_service):
    """Test correct document path structure"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    expected_path = f"house_1/{test_house.id}/documents/test.pdf"
    mock_minio_service.upload_file.return_value = {
        "file_path": expected_path,
        "file_size": len(file_content),
        "etag": "test-etag"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Verify path structure
    assert response.status_code == 200
    data = response.json()
    
    # Verify MinIO was called with correct path
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args
    uploaded_path = call_args[1].get("file_path") or call_args[0][1]
    
    # Path should follow pattern: tenant_id/house_id/documents/filename
    assert "house_1" in uploaded_path
    assert str(test_house.id) in uploaded_path
    assert "documents" in uploaded_path

def test_document_filename_sanitization(db_session, test_user, test_house, mock_minio_service):
    """Test filename sanitization"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file with problematic filename
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "file_path": f"house_1/{test_house.id}/documents/sanitized_filename.pdf",
        "file_size": len(file_content),
        "etag": "test-etag"
    }
    
    # Upload file with problematic filename
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("../../../malicious<script>.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Filename should be sanitized
    assert "malicious" in data["filename"]
    assert "<script>" not in data["filename"]
    assert ".." not in data["filename"]

def test_document_size_validation(db_session, test_user, test_house, mock_minio_service):
    """Test document size validation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create large file (exceeds limit)
    large_content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    file_data = io.BytesIO(large_content)
    
    # Upload large file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large_file.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Should be rejected due to size
    assert response.status_code == 413  # Payload Too Large

def test_document_type_validation(db_session, test_user, test_house, mock_minio_service):
    """Test document type validation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create executable file
    file_content = b"#!/bin/bash\necho 'malicious'"
    file_data = io.BytesIO(file_content)
    
    # Upload executable file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.sh", file_data, "application/x-sh")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Should be rejected due to file type
    assert response.status_code == 400  # Bad Request

def test_document_metadata_storage(db_session, test_user, test_house, mock_minio_service):
    """Test document metadata storage"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "file_path": f"house_1/{test_house.id}/documents/test.pdf",
        "file_size": len(file_content),
        "etag": "test-etag"
    }
    
    # Upload file with metadata
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={
            "house_id": test_house.id,
            "description": "Test document description",
            "tags": "test,document,pdf"
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Test document description"
    assert "test" in data["tags"]
    assert "document" in data["tags"]

def test_document_download(db_session, test_user, test_house, mock_minio_service):
    """Test document download"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document in database
    document = Document(
        filename="test.pdf",
        file_path=f"house_1/{test_house.id}/documents/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        tenant_id="house_1",
        house_id=test_house.id
    )
    db_session.add(document)
    db_session.commit()
    
    # Mock MinIO download
    file_content = b"Test document content"
    mock_minio_service.download_file.return_value = file_content
    
    # Download document
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.content == file_content

def test_document_encryption_decryption():
    """Test file encryption and decryption"""
    
    # Test content
    original_content = b"This is sensitive content that needs encryption"
    
    # Encrypt content
    encrypted_content = encrypt_file(original_content)
    
    # Verify content is encrypted
    assert encrypted_content != original_content
    
    # Decrypt content
    decrypted_content = decrypt_file(encrypted_content)
    
    # Verify decryption works
    assert decrypted_content == original_content

def test_document_tenant_isolation(db_session, test_user, test_house, mock_minio_service):
    """Test document tenant isolation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test file
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    # Mock MinIO upload
    mock_minio_service.upload_file.return_value = {
        "file_path": f"house_1/{test_house.id}/documents/test.pdf",
        "file_size": len(file_content),
        "etag": "test-etag"
    }
    
    # Upload file
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={"house_id": test_house.id},
        headers=headers
    )
    
    # Verify tenant isolation
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "house_1"
    
    # Verify MinIO path contains tenant
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args
    uploaded_path = call_args[1].get("file_path") or call_args[0][1]
    assert "house_1" in uploaded_path 