import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.user_tenant_role import UserTenantRole
from app.models.user_house import UserHouse
from app.core.security import create_access_token
from app.database import get_db
import io
import uuid
from unittest.mock import patch, MagicMock
from app.models.enums import UserRole
from sqlmodel import select

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
    # Usa UUID per creare email e username unici
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=test_tenant_id,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Assegna ruolo admin nel tenant per i permessi
    user_role = UserTenantRole(
        user_id=user.id,
        tenant_id=test_tenant_id,
        role="admin",
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    
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
    
    # Crea relazione UserHouse per dare accesso all'utente
    user_house = UserHouse(
        user_id=test_user.id,
        house_id=house.id,
        tenant_id=test_tenant_id,
        role_in_house="owner",
        is_active=True
    )
    db_session.add(user_house)
    db_session.commit()
    
    return house

@pytest.fixture
def mock_minio_service():
    with patch('app.routers.document.get_minio_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service

def test_document_upload(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document upload"""
    # Verifica che l'utente abbia accesso alla casa
    user_house_ids = test_user.get_house_ids(test_tenant_id)
    print(f"User house IDs: {user_house_ids}")
    print(f"Test house ID: {test_house.id}")
    
    # Se l'utente non ha accesso alla casa, carica esplicitamente le relazioni
    if not user_house_ids:
        # Carica esplicitamente le relazioni UserHouse
        user_houses = db_session.exec(
            select(UserHouse).where(
                UserHouse.user_id == test_user.id,
                UserHouse.tenant_id == test_tenant_id,
                UserHouse.is_active == True
            )
        ).all()
        print(f"User houses from DB: {user_houses}")
        
        # Verifica che la relazione esista
        assert len(user_houses) > 0, "UserHouse relationship should exist"
        assert user_houses[0].house_id == test_house.id
    
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
    # Verifica che l'utente abbia accesso alla casa
    user_house_ids = test_user.get_house_ids(test_tenant_id)
    print(f"User house IDs: {user_house_ids}")
    print(f"Test house ID: {test_house.id}")
    
    # Se l'utente non ha accesso alla casa, carica esplicitamente le relazioni
    if not user_house_ids:
        # Carica esplicitamente le relazioni UserHouse
        user_houses = db_session.exec(
            select(UserHouse).where(
                UserHouse.user_id == test_user.id,
                UserHouse.tenant_id == test_tenant_id,
                UserHouse.is_active == True
            )
        ).all()
        print(f"User houses from DB: {user_houses}")
        
        # Verifica che la relazione esista
        assert len(user_houses) > 0, "UserHouse relationship should exist"
        assert user_houses[0].house_id == test_house.id
    
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
    print(f"Response data: {data}")
    assert len(data) == 1
    assert data[0]["title"] == "Test Document"

def test_document_get(db_session, test_user, test_house, test_tenant_id):
    """Test get single document"""
    # Verifica che l'utente abbia accesso alla casa
    user_house_ids = test_user.get_house_ids(test_tenant_id)
    print(f"User house IDs: {user_house_ids}")
    print(f"Test house ID: {test_house.id}")
    
    # Se l'utente non ha accesso alla casa, carica esplicitamente le relazioni
    if not user_house_ids:
        # Carica esplicitamente le relazioni UserHouse
        user_houses = db_session.exec(
            select(UserHouse).where(
                UserHouse.user_id == test_user.id,
                UserHouse.tenant_id == test_tenant_id,
                UserHouse.is_active == True
            )
        ).all()
        print(f"User houses from DB: {user_houses}")
        
        # Verifica che la relazione esista
        assert len(user_houses) > 0, "UserHouse relationship should exist"
        assert user_houses[0].house_id == test_house.id
    
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

def test_document_delete(db_session, test_user, test_house, mock_minio_service, test_tenant_id):
    """Test document delete"""
    # Verifica che l'utente abbia accesso alla casa
    user_house_ids = test_user.get_house_ids(test_tenant_id)
    print(f"User house IDs: {user_house_ids}")
    print(f"Test house ID: {test_house.id}")
    
    # Se l'utente non ha accesso alla casa, carica esplicitamente le relazioni
    if not user_house_ids:
        # Carica esplicitamente le relazioni UserHouse
        user_houses = db_session.exec(
            select(UserHouse).where(
                UserHouse.user_id == test_user.id,
                UserHouse.tenant_id == test_tenant_id,
                UserHouse.is_active == True
            )
        ).all()
        print(f"User houses from DB: {user_houses}")
        
        # Verifica che la relazione esista
        assert len(user_houses) > 0, "UserHouse relationship should exist"
        assert user_houses[0].house_id == test_house.id
    
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": str(test_tenant_id)
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usa un file_url interno valido per MinIO
    document = Document(
        title="Test Document",
        file_url=f"houses/{test_house.id}/documents/test.pdf",  # Path interno valido
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
    
    # Configura il mock per delete_file per restituire True (successo)
    print(f"Configurando mock per delete_file...")
    mock_minio_service.delete_file.return_value = True
    print(f"Mock configurato: {mock_minio_service.delete_file}")
    
    response = client.delete(f"/api/v1/documents/{document.id}", headers=headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    # Verifica se il mock è stato chiamato
    print(f"Mock chiamato: {mock_minio_service.delete_file.called}")
    print(f"Mock chiamato con: {mock_minio_service.delete_file.call_args_list}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Documento eliminato con successo"
    
    # Verifica che il mock sia stato chiamato con i parametri corretti
    mock_minio_service.delete_file.assert_called_once_with(
        storage_path=f"houses/{test_house.id}/documents/test.pdf",
        tenant_id=test_tenant_id
    ) 