import pytest
from fastapi import UploadFile
from io import BytesIO
import hashlib
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import boto3
from botocore.exceptions import ClientError
import asyncio

from app.core.storage.minio import MinioClient
from app.models.document import Document
from app.core.config import settings

# Fixtures
@pytest.fixture
def sample_file_bytes():
    """Fixture che fornisce un file di test in memoria."""
    return b"Test file content"

@pytest.fixture
def sample_upload_file(sample_file_bytes):
    """Fixture che fornisce un UploadFile di test."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.read = AsyncMock(return_value=sample_file_bytes)
    return mock_file

@pytest.fixture
def minio_test_client():
    """Fixture che fornisce un client MinIO di test."""
    with patch('boto3.client') as mock_client:
        mock_s3 = MagicMock()
        # Mock delle eccezioni boto3
        class FakeClientError(Exception):
            def __init__(self, response, operation_name):
                self.response = response
                self.operation_name = operation_name
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.ClientError = FakeClientError
        mock_client.return_value = mock_s3
        client = MinioClient()
        yield client

@pytest.fixture
def create_test_document():
    """Factory per creare oggetti Document di test."""
    def _create_document(**kwargs):
        content = kwargs.get("content", b"Test file content")
        defaults = {
            "name": "test.txt",
            "type": "text/plain",
            "size": len(content),
            "path": "1/1.txt",
            "checksum": hashlib.sha256(content).hexdigest(),
            "house_id": 1
        }
        defaults.update(kwargs)
        return Document(**defaults)
    return _create_document

# Test Cases
@pytest.mark.asyncio
async def test_upload_file_success(minio_test_client, sample_upload_file):
    """Test del caricamento file con successo."""
    url, checksum = await minio_test_client.upload_file(sample_upload_file)
    
    # Verifica che il file sia stato caricato correttamente
    minio_test_client.s3_client.put_object.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key=sample_upload_file.filename,
        Body=await sample_upload_file.read(),
        ContentType=sample_upload_file.content_type,
        Metadata={'checksum': checksum}
    )
    
    # Verifica che l'URL sia corretto
    expected_url = f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{sample_upload_file.filename}"
    assert url == expected_url
    
    # Verifica che il checksum sia corretto
    expected_checksum = hashlib.md5(await sample_upload_file.read()).hexdigest()
    assert checksum == expected_checksum

@pytest.mark.asyncio
async def test_download_file_success(minio_test_client, sample_file_bytes):
    """Test del download file con successo."""
    # Configura il mock per il download
    mock_response = MagicMock()
    mock_response.__getitem__.side_effect = lambda k: {'Body': MagicMock(read=MagicMock(return_value=sample_file_bytes))}[k] if k == 'Body' else None
    mock_response.get.return_value = {'checksum': hashlib.md5(sample_file_bytes).hexdigest()}
    minio_test_client.s3_client.get_object.return_value = mock_response
    
    # Esegui il download
    content, checksum = await minio_test_client.download_file("test.txt")
    
    # Verifica che il file sia stato scaricato correttamente
    minio_test_client.s3_client.get_object.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key="test.txt"
    )
    
    # Verifica il contenuto e il checksum
    assert content == sample_file_bytes
    assert checksum == hashlib.md5(sample_file_bytes).hexdigest()

def test_object_exists_for_existing_file(minio_test_client):
    """Test della verifica di esistenza per un file esistente."""
    assert minio_test_client.object_exists("test.txt") is True
    minio_test_client.s3_client.head_object.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key="test.txt"
    )

def test_object_exists_for_missing_file(minio_test_client):
    """Test della verifica di esistenza per un file mancante."""
    # Simula l'errore 404 con una vera ClientError di boto3
    error = ClientError({'Error': {'Code': '404'}}, 'HeadObject')
    minio_test_client.s3_client.head_object.side_effect = error
    result = minio_test_client.object_exists("nonexistent.txt")
    assert result is False

def test_delete_file(minio_test_client):
    """Test dell'eliminazione di un file."""
    minio_test_client.delete_file("test.txt")
    minio_test_client.s3_client.delete_object.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key="test.txt"
    )

@pytest.mark.asyncio
async def test_upload_file_with_same_name_overwrite(minio_test_client, sample_upload_file):
    """Test del caricamento di un file con lo stesso nome (overwrite)."""
    # Carica il file due volte
    await minio_test_client.upload_file(sample_upload_file)
    await minio_test_client.upload_file(sample_upload_file)
    
    # Verifica che il file sia stato caricato due volte
    assert minio_test_client.s3_client.put_object.call_count == 2

def test_invalid_credentials():
    """Test della gestione di credenziali non valide."""
    with patch('boto3.client') as mock_client:
        mock_client.side_effect = Exception("Invalid credentials")
        with pytest.raises(Exception) as exc_info:
            MinioClient()
        assert "Invalid credentials" in str(exc_info.value)

@pytest.mark.asyncio
async def test_checksum_mismatch_detection(minio_test_client, sample_file_bytes):
    """Test del rilevamento di un checksum non corrispondente."""
    # Configura il mock per simulare un checksum non corrispondente
    mock_response = MagicMock()
    mock_response.__getitem__.side_effect = lambda k: {'Body': MagicMock(read=MagicMock(return_value=sample_file_bytes))}[k] if k == 'Body' else None
    mock_response.get.return_value = {'checksum': 'invalid_checksum'}
    minio_test_client.s3_client.get_object.return_value = mock_response
    
    # Verifica che venga sollevata un'eccezione
    with pytest.raises(ValueError) as exc_info:
        await minio_test_client.download_file("test.txt")
    assert "File integrity check failed" in str(exc_info.value)

def test_lifecycle_policy_setup(minio_test_client):
    """Test della configurazione delle policy di lifecycle."""
    minio_test_client.s3_client.put_bucket_lifecycle_configuration.reset_mock()
    minio_test_client._setup_lifecycle_policy()
    minio_test_client.s3_client.put_bucket_lifecycle_configuration.assert_called_once()
    
    # Verifica che la configurazione sia corretta
    call_args = minio_test_client.s3_client.put_bucket_lifecycle_configuration.call_args[1]
    assert call_args['Bucket'] == settings.MINIO_BUCKET_NAME
    assert call_args['LifecycleConfiguration']['Rules'][0]['Expiration']['Days'] == settings.MINIO_LIFECYCLE_DAYS

def test_ssl_configuration():
    """Test della configurazione SSL."""
    with patch('boto3.client') as mock_client:
        client = MinioClient()
        mock_client.assert_called_once()
        call_args = mock_client.call_args[1]
        assert call_args['use_ssl'] == settings.MINIO_USE_SSL
        assert call_args['verify'] is True

@pytest.mark.asyncio
async def test_document_model_integrity_after_upload(minio_test_client, sample_upload_file, create_test_document):
    """Verifica che i metadati salvati nel modello Document siano coerenti."""
    test_content = await sample_upload_file.read()
    minio_path, checksum = await minio_test_client.upload_file(sample_upload_file, object_name="1/1.txt")
    document = create_test_document(
        id=1,
        path=minio_path,
        checksum=checksum,
        content=test_content
    )
    expected_url = f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/1/1.txt"
    assert document.path == expected_url
    assert document.checksum == hashlib.md5(test_content).hexdigest()
    assert document.size == len(test_content)
    assert document.type == "text/plain"
    assert document.name == "test.txt" 