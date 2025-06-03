import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import io
import uuid
import traceback

from app.main import app, get_minio_service
from app.services.minio_service import MinioService
from app.models.document import Document
from app.core.config import settings
from app.db.session import get_session

client = TestClient(app)

@pytest.fixture
def sample_file():
    return io.BytesIO(b"test file content")

@pytest.fixture
def mock_minio_service():
    with patch("app.services.minio_service.Minio") as mock_minio:
        client = MagicMock()
        mock_minio.return_value = client
        client.bucket_exists.return_value = True
        client.put_object.return_value = None
        client.presigned_get_object.return_value = "http://test-url"
        client.get_presigned_put_url.return_value = "http://test-url/presigned"
        client.get_presigned_get_url.return_value = "http://test-url/download"
        client.get_file_checksum.return_value = "test-checksum"
        
        def upload_file_side_effect(data, filename, content_type):
            return f"test-path/{filename}"
        
        client.upload_file.side_effect = upload_file_side_effect
        yield client

@pytest.fixture
def override_minio_service(mock_minio_service):
    """Override la dependency get_minio_service di FastAPI con il mock."""
    app.dependency_overrides[get_minio_service] = lambda: mock_minio_service
    yield
    app.dependency_overrides.pop(get_minio_service, None)

@pytest.fixture(autouse=True)
def override_get_session(document_table):
    """Override la dependency get_session per usare la sessione di test."""
    app.dependency_overrides[get_session] = lambda: document_table
    yield
    app.dependency_overrides.pop(get_session, None)

def test_upload_document_success(sample_file, mock_minio_service, document_table, override_minio_service):
    """Test 2.2.3.1: POST /documents/upload - Success"""
    # Preparazione
    file_name = "test.pdf"
    file_content = b"test file content"
    file = ("test.pdf", io.BytesIO(file_content), "application/pdf")
    
    # Configura il mock per accettare gli argomenti
    def mock_upload_side_effect(file_data, object_name, content_type):
        return f"test-path/{object_name}"
    
    mock_minio_service.upload_file.side_effect = mock_upload_side_effect
    
    # Esecuzione
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    
    # Verifiche
    if response.status_code != 200:
        print("\n=== Error Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("=== Stack Trace ===")
        print(traceback.format_exc())
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica struttura risposta
    assert "filename" in data
    assert "content_type" in data
    assert "document_id" in data
    
    # Verifica valori
    assert data["filename"] == file_name
    assert data["content_type"] == "application/pdf"
    assert isinstance(data["document_id"], int)
    
    # Verifica chiamate MinIO
    mock_minio_service.upload_file.assert_called_once()
    call_args = mock_minio_service.upload_file.call_args[0]
    assert call_args[0] == file_content  # Verifica il contenuto del file
    assert call_args[2] == "application/pdf"  # Verifica il content type

def test_upload_document_no_file(mock_minio_service, override_minio_service):
    """Test 2.2.3.2: POST /documents/upload - No File"""
    # Esecuzione
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    
    # Verifiche
    assert response.status_code == 422
    assert "detail" in response.json()
    mock_minio_service.upload_file.assert_not_called()

def test_upload_document_large_file(sample_file, mock_minio_service, document_table, override_minio_service):
    """Test 2.2.3.3: MinIO Link Check - Large File"""
    # Preparazione
    file_name = "large.pdf"
    file_content = b"x" * (settings.MAX_DIRECT_UPLOAD_SIZE + 1)  # File più grande del limite
    file = (file_name, io.BytesIO(file_content), "application/pdf")
    
    # Configurazione mock per pre-signed URL
    presigned_url = "http://test-url/presigned"
    mock_minio_service.get_presigned_put_url.return_value = presigned_url
    
    # Esecuzione
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    
    # Verifiche
    if response.status_code != 200:
        print("\n=== Error Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("=== Stack Trace ===")
        print(traceback.format_exc())
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica struttura risposta
    assert "upload_url" in data
    assert "filename" in data
    assert "content_type" in data
    assert "document_id" in data
    
    # Verifica valori
    assert data["upload_url"] == presigned_url
    assert data["filename"].endswith(".pdf")
    assert data["content_type"] == "application/pdf"
    assert data["document_id"] is None  # Per file grandi non abbiamo ancora un document_id
    
    # Verifica che non sia stato fatto l'upload diretto
    mock_minio_service.upload_file.assert_not_called()
    
    # Verifica che sia stato generato il pre-signed URL
    mock_minio_service.get_presigned_put_url.assert_called_once()
    # Controlla che il nome generato abbia estensione .pdf
    presigned_args = mock_minio_service.get_presigned_put_url.call_args[0]
    assert presigned_args[0].endswith('.pdf')

def test_upload_document_invalid_file_type(sample_file, mock_minio_service, override_minio_service):
    """Test aggiuntivo: Upload con tipo file non valido"""
    # Preparazione
    file_name = "test.exe"
    file_content = b"test file content"
    file = (file_name, io.BytesIO(file_content), "application/octet-stream")
    
    # Esecuzione
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    
    # Verifiche
    if response.status_code != 400:
        print("\n=== Error Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("=== Stack Trace ===")
        print(traceback.format_exc())
    
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "file type" in response.json()["detail"].lower()
    mock_minio_service.upload_file.assert_not_called()

def test_upload_document_minio_error(sample_file, mock_minio_service, document_table, override_minio_service):
    """Test aggiuntivo: Errore MinIO durante l'upload"""
    # Preparazione
    file_name = "test.pdf"
    file_content = b"test file content"
    file = (file_name, io.BytesIO(file_content), "application/pdf")
    
    # Simula errore MinIO
    mock_minio_service.upload_file.side_effect = Exception("MinIO error")
    
    # Esecuzione
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file},
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    
    # Verifiche
    if response.status_code != 500:
        print("\n=== Error Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("=== Stack Trace ===")
        print(traceback.format_exc())
    
    assert response.status_code == 500
    assert "detail" in response.json()
    mock_minio_service.upload_file.assert_called_once() 