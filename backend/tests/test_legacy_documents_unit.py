import io
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.legacy_documents import LegacyDocument
from backend.models.user import User
from datetime import datetime
from sqlalchemy.orm import Session

client = TestClient(app)

@pytest.fixture
def mock_auth():
    """Mock per l'autenticazione"""
    with patch("backend.routers.legacy_documents.get_current_user") as mock:
        mock.return_value = User(
            id=1,
            email="test@example.com",
            is_active=1,
            role="user",
            full_name="Test User",
            hashed_password="hashed_password"
        )
        yield mock

@pytest.fixture
def mock_db():
    """Mock per la sessione del database"""
    mock_session = Mock(spec=Session)
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    mock_session.query = Mock()
    return mock_session

@pytest.fixture
def mock_minio_client():
    """Mock per il client MinIO"""
    with patch("backend.utils.minio.get_minio_client") as mock:
        yield mock

@pytest.fixture
def mock_upload_file():
    """Mock per la funzione di upload file"""
    with patch("backend.utils.minio.upload_file_to_minio") as mock:
        mock.return_value = "https://minio.example.com/test.pdf"
        yield mock

@pytest.fixture
def mock_token():
    """Mock per il token di autenticazione"""
    with patch("backend.utils.auth.oauth2_scheme") as mock:
        mock.return_value = "test_token"
        yield mock

@pytest.fixture
def mock_jwt():
    """Mock per la decodifica del token JWT"""
    with patch("backend.utils.auth.jwt.decode") as mock:
        mock.return_value = {"sub": "test@example.com"}
        yield mock

class TestLegacyDocuments:
    def test_create_legacy_document(
        self,
        mock_db,
        mock_minio_client,
        mock_upload_file,
        mock_auth,
        mock_token,
        mock_jwt
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
    
        # Mock del documento creato
        created_document = LegacyDocument(
            id=1,
            house_id=1,
            node_id=2,
            type="PDF",
            version="1.0",
            file_url="https://minio.example.com/test.pdf",
            filename="test.pdf",
            created_at=datetime.now()
        )
        mock_db.refresh.return_value = created_document

        # Mock della dependency get_db
        with patch("backend.db.session.get_db", return_value=mock_db):
            # Esegui la richiesta
            response = client.post(
                "/legacy-documents",
                files={"file": ("test.pdf", test_file, "application/pdf")},
                data=form_data,
                headers={"Authorization": "Bearer test_token"}
            )
    
            # Verifica la risposta
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["type"] == "PDF"
            assert data["version"] == "1.0"
            assert data["file_url"] == "https://minio.example.com/test.pdf"
            assert data["filename"] == "test.pdf"
            assert "created_at" in data

    def test_get_legacy_documents(
        self,
        mock_db,
        mock_auth,
        mock_token,
        mock_jwt
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
                filename="doc1.pdf",
                version="1.0",
                created_at=datetime.now()
            ),
            LegacyDocument(
                id=2,
                house_id=1,
                node_id=2,
                type="JPG",
                file_url="https://minio.example.com/doc2.jpg",
                filename="doc2.jpg",
                version="2.0",
                created_at=datetime.now()
            )
        ]
    
        # Mock della query del database
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = test_documents
        mock_db.query.return_value = mock_query

        # Mock della dependency get_db
        with patch("backend.db.session.get_db", return_value=mock_db):
            # Esegui la richiesta
            response = client.get(
                "/legacy-documents/2",
                headers={"Authorization": "Bearer test_token"}
            )

            # Verifica la risposta
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[0]["type"] == "PDF"
            assert data[1]["id"] == 2
            assert data[1]["type"] == "JPG" 