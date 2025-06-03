import pytest
pytestmark = pytest.mark.usefixtures("create_test_db")

from unittest.mock import patch, MagicMock
import io
import traceback

from app.services.minio_service import MinioService
from app.models.document import Document
from app.core.config import settings
from app.models.user import User
from app.core.auth import get_current_user

@pytest.fixture
def mock_current_user():
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        is_active=True
    )
    return user

@pytest.fixture
def override_get_current_user(mock_current_user):
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def mock_minio_service():
    with patch("app.services.minio_service.Minio") as mock_minio:
        client = MagicMock()
        mock_minio.return_value = client
        client.bucket_exists.return_value = True
        client.get_presigned_get_url.return_value = "http://test-url/download"
        yield client

@pytest.fixture
def override_minio_service(mock_minio_service):
    from app.main import app, get_minio_service
    app.dependency_overrides[get_minio_service] = lambda: mock_minio_service
    yield
    app.dependency_overrides.pop(get_minio_service, None)

def test_download_document_success(mock_minio_service, document_table, override_minio_service, override_get_current_user, mock_current_user, client):
    """Test 2.2.4.1: GET /documents/download/{id} - Success"""
    document = Document(
        name="test.pdf",
        type="application/pdf",
        size=1024,
        path="test/path/test.pdf",
        checksum="test-checksum",
        user_id=mock_current_user.id
    )
    document_table.add(document)
    document_table.commit()
    document_table.refresh(document)
    download_url = "http://test-url/download"
    mock_minio_service.get_presigned_get_url.return_value = download_url
    response = client.get(
        f"/api/v1/documents/download/{document.id}",
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    if response.status_code != 200:
        print("\n=== Error Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("=== Stack Trace ===")
        print(traceback.format_exc())
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert data["download_url"] == download_url
    mock_minio_service.get_presigned_get_url.assert_called_once_with(document.path)

def test_download_document_unauthorized(mock_minio_service, document_table, override_minio_service, client):
    response = client.get("/api/v1/documents/download/1")
    assert response.status_code == 401
    assert "detail" in response.json()
    mock_minio_service.get_presigned_get_url.assert_not_called()
    response = client.get(
        "/api/v1/documents/download/1",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()
    mock_minio_service.get_presigned_get_url.assert_not_called()

def test_download_document_not_found(mock_minio_service, document_table, override_minio_service, override_get_current_user, client):
    response = client.get(
        "/api/v1/documents/download/999",
        headers={"Authorization": f"Bearer {settings.TEST_TOKEN}"}
    )
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"].lower()
    mock_minio_service.get_presigned_get_url.assert_not_called() 