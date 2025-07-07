import pytest
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
import io
import uuid
import time
from unittest.mock import patch, MagicMock
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
def test_permissions(db_session, test_tenant_id, test_user):
    """Create test permissions and assign them to user"""
    # Create unique names to avoid duplicates
    timestamp = int(time.time() * 1000)
    
    # Create permissions with unique names
    permissions = [
        Permission(
            name=f"read_documents_{timestamp}",
            resource="documents",
            action="read",
            is_active=True
        ),
        Permission(
            name=f"write_documents_{timestamp}", 
            resource="documents",
            action="write",
            is_active=True
        ),
        Permission(
            name=f"delete_documents_{timestamp}",
            resource="documents", 
            action="delete",
            is_active=True
        )
    ]
    
    for perm in permissions:
        db_session.add(perm)
    db_session.commit()
    
    # Create role with unique name
    role = Role(
        name=f"document_manager_{timestamp}",
        description="Role for document management",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    # Assign admin role to user in tenant (admin has all permissions)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    return permissions

@pytest.fixture
def mock_minio_service():
    """Mock MinIO service"""
    with patch('app.routers.document.get_minio_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

def test_document_upload_success(db_session, test_user, test_house, test_permissions, mock_minio_service, test_tenant_id):
    """Test successful document upload"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create access token with the correct tenant_id
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
    
    # Ensure the mock is properly configured
    print(f"Mock MinIO service: {mock_minio_service}")
    print(f"Mock upload_file method: {mock_minio_service.upload_file}")
    
    # Upload file
    try:
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
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.text}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["file_size"] == len(file_content)
        assert data["file_type"] == "application/pdf"
        assert data["tenant_id"] == str(test_tenant_id)
        assert data["house_id"] == test_house.id
        
    except Exception as e:
        print(f"Exception during test: {e}")
        raise

def test_document_list(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test document listing"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document
    document = Document(
        title="Test Document",
        description="Test description",
        file_url="test/path.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document)
    db_session.commit()
    
    # List documents
    response = client.get(
        "/api/v1/documents/",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Document"
    assert data[0]["tenant_id"] == str(test_tenant_id)

def test_document_get(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test get single document"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document
    document = Document(
        title="Test Document",
        description="Test description",
        file_url="test/path.pdf",
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
    
    # Get document
    response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["id"] == document.id

def test_document_update(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test document update"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document
    document = Document(
        title="Original Title",
        description="Original description",
        file_url="test/path.pdf",
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
    
    # Update document
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    
    response = client.put(
        f"/api/v1/documents/{document.id}",
        json=update_data,
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"

def test_document_delete(db_session, test_user, test_house, test_permissions, mock_minio_service, test_tenant_id):
    """Test document deletion"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test document with valid path structure
    document = Document(
        title="Test Document",
        description="Test description",
        file_url=f"houses/{test_house.id}/documents/test_document.pdf",
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
    
    # Mock MinIO delete response
    mock_minio_service.delete_file.return_value = True
    
    # Delete document
    response = client.delete(
        f"/api/v1/documents/{document_id}",
        headers=headers
    )
    
    # Aggiorna la sessione per evitare cache
    db_session.expire_all()
    
    # Verify response
    assert response.status_code == 200
    
    # Verify document is deleted
    deleted_document = db_session.get(Document, document_id)
    assert deleted_document is None

def test_document_tenant_isolation(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test document tenant isolation"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create second tenant
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
    
    # Create document for first tenant
    document1 = Document(
        title="First Tenant Document",
        file_url=f"houses/{test_house.id}/documents/first_tenant_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum1",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document1)
    
    # Create document for second tenant
    document2 = Document(
        title="Second Tenant Document",
        file_url=f"houses/{second_house.id}/documents/second_tenant_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum2",
        tenant_id=second_tenant_id,
        house_id=second_house.id,
        owner_id=second_user.id
    )
    db_session.add(document2)
    
    db_session.commit()
    
    # Create access token for first tenant
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List documents for first tenant
    response = client.get(
        "/api/v1/documents/",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "First Tenant Document"
    assert data[0]["tenant_id"] == str(test_tenant_id)

def test_document_house_filtering(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test document filtering by house"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create second house
    second_house = House(
        name="Second House",
        address="Via Second 1",
        tenant_id=test_tenant_id,
        owner_id=test_user.id
    )
    db_session.add(second_house)
    db_session.commit()
    db_session.refresh(second_house)
    
    # Create documents for different houses
    document1 = Document(
        title="First House Document",
        file_url=f"houses/{test_house.id}/documents/first_house_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum1",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document1)
    
    document2 = Document(
        title="Second House Document",
        file_url=f"houses/{second_house.id}/documents/second_house_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum2",
        tenant_id=test_tenant_id,
        house_id=second_house.id,
        owner_id=test_user.id
    )
    db_session.add(document2)
    
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List documents filtered by first house
    response = client.get(
        f"/api/v1/documents/?house_id={test_house.id}",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "First House Document"
    assert data[0]["house_id"] == test_house.id

def test_document_type_filtering(db_session, test_user, test_house, test_permissions, test_tenant_id):
    """Test document filtering by type"""
    
    # Associa ruolo admin all'utente nel tenant (RBAC)
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()
    
    # Create documents of different types
    document1 = Document(
        title="Contract Document",
        document_type="contract",
        file_url=f"houses/{test_house.id}/documents/contract_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum1",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document1)
    
    document2 = Document(
        title="General Document",
        document_type="general",
        file_url=f"houses/{test_house.id}/documents/general_doc.pdf",
        file_size=100,
        file_type="application/pdf",
        checksum="test_checksum2",
        tenant_id=test_tenant_id,
        house_id=test_house.id,
        owner_id=test_user.id
    )
    db_session.add(document2)
    
    db_session.commit()
    
    # Create access token with the correct tenant_id
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List documents filtered by type
    response = client.get(
        "/api/v1/documents/?document_type=contract",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Contract Document"
    assert data[0]["document_type"] == "contract" 