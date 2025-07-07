import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.security import create_access_token
from app.database import get_db
import io
import uuid
from unittest.mock import patch, MagicMock
from app.models.enums import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()

@pytest.fixture
def test_user(db_session, test_tenant_id):
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
def test_house(db_session, test_user, test_tenant_id):
    house = House(
        name="Test House",
        address="Via Test 1",
        owner_id=test_user.id,
        tenant_id=test_tenant_id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def mock_minio_service():
    with patch('app.services.minio_service.get_minio_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

def test_document_upload(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document upload"""
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    file_content = b"Test content"
    file_data = io.BytesIO(file_content)
    
    mock_minio_service.upload_file.return_value = {
        "storage_path": f"houses/{test_house.id}/documents/test.pdf",
        "file_size": len(file_content),
        "content_type": "application/pdf"
    }
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        data={
            "title": "Test Document",
            "house_id": test_house.id
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"

def test_document_list(db_session, test_user, test_house, test_tenant_id):
    """Test document listing"""
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    document = Document(
        title="Test Document",
        file_url="https://example.com/test.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="abc123",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    
    response = client.get("/api/v1/documents/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Document"

def test_document_get(db_session, test_user, test_house, test_tenant_id):
    """Test get single document"""
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    document = Document(
        title="Test Document",
        file_url="https://example.com/test.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="abc123",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    response = client.get(f"/api/v1/documents/{document.id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["id"] == document.id

def test_document_update(db_session, test_user, test_house, test_tenant_id):
    """Test document update"""
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    document = Document(
        title="Original Title",
        file_url="https://example.com/test.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="abc123",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    
    response = client.put(
        f"/api/v1/documents/{document.id}",
        json=update_data,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

def test_document_delete(db_session, test_user, test_house, test_tenant_id):
    """Test document deletion"""
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    document = Document(
        title="Test Document",
        file_url="https://example.com/test.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="abc123",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    response = client.delete(f"/api/v1/documents/{document.id}", headers=headers)
    
    assert response.status_code == 200
    
    # Verify document is deleted
    deleted_document = db_session.get(Document, document.id)
    assert deleted_document is None 