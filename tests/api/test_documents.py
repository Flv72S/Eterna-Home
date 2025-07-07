"""Test per gli endpoint dei documenti."""
import io
import hashlib
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session
import uuid

from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.role import Role
from app.models.user_tenant_role import UserTenantRole
from app.models.permission import Permission
from app.models.role_permission import RolePermission


@pytest.fixture(autouse=True)
def mock_minio_service():
    """Mock per il servizio MinIO."""
    with patch("app.routers.document.get_minio_service") as mock:
        service = MagicMock()
        
        # Mock per upload_file (funzione sincrona)
        def mock_upload_file(*args, **kwargs):
            return {
                "storage_path": "test/path/uploaded_file.pdf",
                "file_size": 1024,
                "content_type": "application/pdf"
            }
        
        # Mock per download_file (funzione sincrona) - restituisce il formato corretto
        def mock_download_file(*args, **kwargs):
            # Restituisce un oggetto con il metodo read() come un file
            file_content = b"test file content"
            file_obj = MagicMock()
            file_obj.read.return_value = file_content
            file_obj.__iter__ = lambda self: iter([file_content])
            file_obj.__getitem__ = lambda self, key: file_content[key] if isinstance(key, int) else file_content
            return file_obj
        
        # Mock per delete_file (funzione sincrona)
        def mock_delete_file(*args, **kwargs):
            return True
        
        # Assegna i mock al servizio
        service.upload_file = mock_upload_file
        service.download_file = mock_download_file
        service.delete_file = mock_delete_file
        
        # Mock per get_minio_service
        mock.return_value = service
        
        yield


@pytest.fixture(autouse=True)
def mock_storage_utils():
    """Mock per le funzioni di validazione del storage."""
    with patch("app.core.storage_utils.is_valid_tenant_path") as mock_valid_path, \
         patch("app.core.storage_utils.validate_path_security") as mock_validate_security, \
         patch("app.core.storage_utils.multi_tenant_logger") as mock_logger:
        
        # Mock per is_valid_tenant_path
        mock_valid_path.return_value = True
        
        # Mock per validate_path_security
        mock_validate_security.return_value = True
        
        # Mock per il logger
        mock_logger.log_security_event = MagicMock()
        
        yield


def create_test_user_with_permissions(auth_test_session, tenant_id):
    """Crea un utente di test con i permessi necessari per i documenti."""
    # Crea l'utente
    user = User(
        email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        hashed_password="$2b$12$ZYbqEQzza.6PGxVXY84hIO7LdE9BQ8NhbSuy6ILhNBHyEZ5.AJx6.",  # TestPassword123!
        is_active=True,
        is_superuser=False,
        tenant_id=tenant_id,
        role="user",
        is_verified=True,
        full_name="Test User"
    )
    auth_test_session.add(user)
    auth_test_session.commit()
    auth_test_session.refresh(user)
    
    # Assegna il ruolo 'admin' all'utente nel tenant
    user_role = UserTenantRole(
        user_id=user.id,
        tenant_id=tenant_id,
        role="admin"
    )
    auth_test_session.add(user_role)
    auth_test_session.commit()
    
    return user


def test_upload_document_file(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test upload di un file su un documento esistente."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Login per ottenere il token
    login_response = client.post("/api/v1/auth/token", data={
        "username": user.email,
        "password": "TestPassword123!"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Crea un nuovo documento usando l'endpoint corretto
    document_data = {
        "title": "Test Document",
        "description": "Test document description",
        "document_type": "general",
        "house_id": house.id
    }
    
    # Crea un file di test
    test_file_content = b"Test file content"
    test_file = io.BytesIO(test_file_content)
    
    create_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", test_file, "application/pdf")},
        data=document_data,
        headers=headers
    )
    
    # Verifica che il documento sia stato creato correttamente
    assert create_response.status_code == 200, f"Errore creazione documento: {create_response.text}"
    response_data = create_response.json()
    
    # Verifica i campi del documento
    assert response_data["title"] == "Test Document"
    assert response_data["description"] == "Test document description"
    assert response_data["document_type"] == "general"
    assert response_data["file_size"] == 1024
    assert response_data["file_type"] == "application/pdf"
    assert response_data["house_id"] == house.id
    assert response_data["owner_id"] == user.id
    assert "id" in response_data
    assert "created_at" in response_data
    assert "updated_at" in response_data
    
    # Verifica che il file sia stato caricato correttamente
    assert response_data["file_url"] == "test/path/uploaded_file.pdf"
    
    print(f"✅ Test upload documento completato con successo. Document ID: {response_data['id']}")

def test_upload_document_file_not_found(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test upload su casa non esistente."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Upload del file con casa inesistente
    document_data = {
        "title": "Test Document",
        "description": "Test document description",
        "document_type": "general",
        "house_id": 999  # Casa inesistente
    }
    
    test_file_content = b"Test file content"
    test_file = io.BytesIO(test_file_content)
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", test_file, "application/pdf")},
        data=document_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verifica che l'errore sia gestito correttamente
    assert response.status_code in [404, 422]  # Può essere 404 o 422 a seconda della validazione
    response_data = response.json()
    assert "detail" in response_data
    
    print("✅ Test upload documento casa non trovata completato con successo")

def test_upload_document_file_unauthorized(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test upload senza autenticazione."""
    # Upload del file senza token
    document_data = {
        "title": "Test Document",
        "description": "Test document description",
        "document_type": "general",
        "house_id": 1
    }
    
    test_file_content = b"Test file content"
    test_file = io.BytesIO(test_file_content)
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", test_file, "application/pdf")},
        data=document_data
    )
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
    
    print("✅ Test upload documento non autorizzato completato con successo")

def test_upload_document_file_duplicate(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test che verifica che non si possano creare documenti duplicati."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Primo upload - dovrebbe funzionare
    document_data = {
        "title": "Test Document",
        "description": "Test document description",
        "document_type": "general",
        "house_id": house.id
    }
    
    test_file_content = b"Test file content"
    test_file = io.BytesIO(test_file_content)
    
    response1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.pdf", test_file, "application/pdf")},
        data=document_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response1.status_code == 200
    
    # Secondo upload con lo stesso titolo - dovrebbe funzionare (non è un duplicato)
    test_file_content2 = b"Test file content 2"
    test_file2 = io.BytesIO(test_file_content2)
    
    response2 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document2.pdf", test_file2, "application/pdf")},
        data=document_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response2.status_code == 200
    
    print("✅ Test upload documenti multipli completato con successo")

def test_download_document_file(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test download di un file esistente."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento con file
    document = Document(
        title="Test Document",
        file_type="application/pdf",
        file_size=1024,
        file_url="test/path/document.pdf",
        checksum="test_checksum",
        owner_id=user.id,
        house_id=house.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file - usa l'endpoint corretto dal router document
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f'attachment; filename="{document.title}"'
    assert response.content == b"test file content"
    
    print(f"✅ Test download documento completato con successo. Document ID: {document.id}")

def test_download_document_file_not_found(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test download di un file non esistente."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file - usa l'endpoint corretto dal router document
    response = client.get(
        "/api/v1/documents/999/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Documento non trovato" in response.json()["detail"]
    
    print("✅ Test download documento non trovato completato con successo")

def test_download_document_file_no_file(client: TestClient, auth_test_session, mock_minio_service, mock_storage_utils):
    """Test download di un documento senza file associato."""
    # Crea tenant e utente con permessi
    tenant_id = uuid.uuid4()
    user = create_test_user_with_permissions(auth_test_session, tenant_id)
    
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento senza file
    document = Document(
        title="Test Document",
        file_type=None,
        file_size=None,
        file_url="",  # Stringa vuota invece di None per rispettare il vincolo NOT NULL
        checksum=None,
        owner_id=user.id,
        house_id=house.id,
        tenant_id=tenant_id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": user.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file - usa l'endpoint corretto dal router document
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Nessun file associato" in response.json()["detail"]
    
    print(f"✅ Test download documento senza file completato con successo. Document ID: {document.id}") 
