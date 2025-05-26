import io
from unittest.mock import Mock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models.legacy_documents import LegacyDocument
from backend.utils.auth import get_current_user
from backend.utils.minio import get_minio_client, upload_file_to_minio

client = TestClient(app)

# Mock user for authentication
mock_user = {"email": "test@example.com", "id": 1}

@pytest.fixture
def mock_db():
    """Fixture per mockare la sessione del database"""
    mock_session = Mock(spec=Session)
    return mock_session

@pytest.fixture
def mock_minio_client():
    """Fixture per mockare il client MinIO"""
    with patch("backend.utils.minio.get_minio_client") as mock:
        yield mock

@pytest.fixture
def mock_upload_file():
    """Fixture per mockare l'upload su MinIO"""
    with patch("backend.utils.minio.upload_file_to_minio") as mock:
        mock.return_value = "https://minio.example.com/eterna-legacy/test-file.pdf"
        yield mock

@pytest.fixture
def mock_auth():
    """Fixture per mockare l'autenticazione"""
    with patch("backend.utils.auth.get_current_user") as mock:
        mock.return_value = mock_user
        yield mock

class TestLegacyDocuments:
    def test_create_legacy_document(
        self,
        mock_db,
        mock_minio_client,
        mock_upload_file,
        mock_auth
    ):
        """Test per l'endpoint POST /legacy-documents"""
        # Prepara il file di test
        test_file = io.BytesIO(b"Test file content")
        test_file.name = "test.pdf"
        
        # Prepara i dati del form
        form_data = {
            "house_id": "1",
            "node_id": "2",
            "type": "PDF",
            "version": "1.0"
        }
        
        # Mock della sessione del database
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock della dependency get_db
        with patch("backend.db.session.get_db", return_value=mock_db):
            # Esegui la richiesta
            response = client.post(
                "/legacy-documents",
                files={"file": ("test.pdf", test_file, "application/pdf")},
                data=form_data
            )
            
            # Verifica la risposta
            assert response.status_code == 200
            data = response.json()
            assert data["house_id"] == 1
            assert data["node_id"] == 2
            assert data["type"] == "PDF"
            assert data["version"] == "1.0"
            assert data["file_url"] == "https://minio.example.com/eterna-legacy/test-file.pdf"
            
            # Verifica che upload_file_to_minio sia stato chiamato correttamente
            mock_upload_file.assert_called_once()
            call_args = mock_upload_file.call_args[0]
            assert call_args[1] == "eterna-legacy"  # bucket name
            
            # Verifica che il documento sia stato aggiunto al database
            mock_db.add.assert_called_once()
            added_document = mock_db.add.call_args[0][0]
            assert isinstance(added_document, LegacyDocument)
            assert added_document.house_id == 1
            assert added_document.node_id == 2
            assert added_document.type == "PDF"
            assert added_document.version == "1.0"
            
            # Verifica che le operazioni sul database siano state chiamate
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_get_legacy_documents(
        self,
        mock_db,
        mock_auth
    ):
        """Test per l'endpoint GET /legacy-documents/{node_id}"""
        # Prepara i documenti di test
        test_documents = [
            LegacyDocument(
                id=1,
                house_id=1,
                node_id=2,
                type="PDF",
                file_url="https://minio.example.com/doc1.pdf",
                version="1.0"
            ),
            LegacyDocument(
                id=2,
                house_id=1,
                node_id=2,
                type="JPG",
                file_url="https://minio.example.com/doc2.jpg",
                version="2.0"
            )
        ]
        
        # Mock della query del database
        mock_db.query.return_value.filter.return_value.all.return_value = test_documents
        
        # Mock della dependency get_db
        with patch("backend.db.session.get_db", return_value=mock_db):
            # Esegui la richiesta
            response = client.get("/legacy-documents/2")
            
            # Verifica la risposta
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            
            # Verifica il primo documento
            assert data[0]["id"] == 1
            assert data[0]["house_id"] == 1
            assert data[0]["node_id"] == 2
            assert data[0]["type"] == "PDF"
            assert data[0]["file_url"] == "https://minio.example.com/doc1.pdf"
            assert data[0]["version"] == "1.0"
            
            # Verifica il secondo documento
            assert data[1]["id"] == 2
            assert data[1]["house_id"] == 1
            assert data[1]["node_id"] == 2
            assert data[1]["type"] == "JPG"
            assert data[1]["file_url"] == "https://minio.example.com/doc2.jpg"
            assert data[1]["version"] == "2.0" 