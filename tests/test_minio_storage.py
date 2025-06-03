import pytest
from fastapi import UploadFile
from io import BytesIO
import hashlib
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import ClientError
import asyncio

from app.core.storage.minio import MinioClient
from app.models.document import Document

# Fixtures
@pytest.fixture
def sample_file_bytes():
    """Fixture che fornisce un file di test in memoria."""
    content = b"Test file content"
    return content

@pytest.fixture
def sample_upload_file(sample_file_bytes):
    """Fixture che fornisce un UploadFile di test."""
    async def async_read():
        return sample_file_bytes
    upload = MagicMock()
    upload.filename = "test.txt"
    upload.file = MagicMock()
    upload.content_type = "text/plain"
    upload.read = async_read
    return upload

@pytest.fixture
def minio_test_client():
    """Fixture che fornisce un client MinIO configurato per i test."""
    with patch('boto3.client') as mock_client:
        mock_s3 = Mock()
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
    """Verifica che un file possa essere caricato correttamente su MinIO."""
    # Arrange
    house_id = 1
    document_id = 1
    
    # Act
    minio_path, checksum = await minio_test_client.upload_file(
        sample_upload_file,
        house_id,
        document_id
    )
    
    # Assert
    expected_path = f"{house_id}/{document_id}.txt"
    assert minio_path == expected_path
    assert checksum == hashlib.sha256(b"Test file content").hexdigest()
    
    # Verify MinIO client was called correctly
    minio_test_client.client.put_object.assert_called_once()
    call_args = minio_test_client.client.put_object.call_args[1]
    assert call_args["Bucket"] == minio_test_client.bucket_name
    assert call_args["Key"] == expected_path
    assert call_args["Body"] == b"Test file content"
    assert call_args["ContentType"] == "text/plain"

def test_download_file_success(minio_test_client, sample_file_bytes):
    """Verifica che un file possa essere scaricato correttamente."""
    # Arrange
    minio_path = "1/1.txt"
    minio_test_client.client.get_object.return_value = {
        "Body": BytesIO(sample_file_bytes)
    }
    
    # Act
    downloaded_content = minio_test_client.download_file(minio_path)
    
    # Assert
    assert downloaded_content == sample_file_bytes
    minio_test_client.client.get_object.assert_called_once_with(
        Bucket=minio_test_client.bucket_name,
        Key=minio_path
    )

def test_object_exists_for_existing_file(minio_test_client):
    """Verifica che object_exists ritorni True per un file esistente."""
    # Arrange
    minio_path = "1/1.txt"
    minio_test_client.client.head_object.return_value = {}
    
    # Act
    exists = minio_test_client.object_exists(minio_path)
    
    # Assert
    assert exists is True
    minio_test_client.client.head_object.assert_called_once_with(
        Bucket=minio_test_client.bucket_name,
        Key=minio_path
    )

def test_object_exists_for_missing_file(minio_test_client):
    """Verifica che object_exists ritorni False per un file inesistente."""
    # Arrange
    minio_path = "1/1.txt"
    minio_test_client.client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}},
        "HeadObject"
    )
    
    # Act
    exists = minio_test_client.object_exists(minio_path)
    
    # Assert
    assert exists is False

def test_delete_file(minio_test_client):
    """Verifica che un file venga effettivamente cancellato."""
    # Arrange
    minio_path = "1/1.txt"
    
    # Act
    result = minio_test_client.delete_file(minio_path)
    
    # Assert
    assert result is True
    minio_test_client.client.delete_object.assert_called_once_with(
        Bucket=minio_test_client.bucket_name,
        Key=minio_path
    )

@pytest.mark.asyncio
async def test_upload_file_with_same_name_overwrite(minio_test_client, sample_upload_file):
    """Verifica che un file con lo stesso nome venga sovrascritto correttamente."""
    # Arrange
    house_id = 1
    document_id = 1
    new_content = b"New content"
    async def async_read_new():
        return new_content
    new_file = MagicMock()
    new_file.filename = "test.txt"
    new_file.file = MagicMock()
    new_file.content_type = "text/plain"
    new_file.read = async_read_new
    # Act
    minio_path, checksum = await minio_test_client.upload_file(
        new_file,
        house_id,
        document_id
    )
    # Assert
    expected_path = f"{house_id}/{document_id}.txt"
    assert minio_path == expected_path
    assert checksum == hashlib.sha256(new_content).hexdigest()
    # Verify the file was overwritten
    minio_test_client.client.put_object.assert_called_once()
    call_args = minio_test_client.client.put_object.call_args[1]
    assert call_args["Body"] == new_content

def test_invalid_credentials():
    """Simula un errore di credenziali errate."""
    # Arrange
    with patch('boto3.client') as mock_client:
        mock_client.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessKeyId"}},
            "GetObject"
        )
        
        # Act & Assert
        with pytest.raises(ClientError) as exc_info:
            client = MinioClient()
            client.download_file("test.txt")
        
        assert exc_info.value.response["Error"]["Code"] == "InvalidAccessKeyId"

@pytest.mark.asyncio
async def test_document_model_integrity_after_upload(minio_test_client, sample_upload_file, create_test_document):
    """Verifica che i metadati salvati nel modello Document siano coerenti."""
    # Arrange
    house_id = 1
    document_id = 1
    test_content = b"Test file content"
    # Act
    minio_path, checksum = await minio_test_client.upload_file(
        sample_upload_file,
        house_id,
        document_id
    )
    document = create_test_document(
        id=document_id,
        path=minio_path,
        checksum=checksum,
        content=test_content
    )
    # Assert
    assert document.path == f"{house_id}/{document_id}.txt"
    assert document.checksum == hashlib.sha256(test_content).hexdigest()
    assert document.size == len(test_content)
    assert document.type == "text/plain"
    assert document.name == "test.txt"

def test_checksum_mismatch_detection(minio_test_client, sample_file_bytes):
    """Simula un'alterazione di un file."""
    # Arrange
    minio_path = "1/1.txt"
    altered_content = b"Altered content"
    minio_test_client.client.get_object.return_value = {
        "Body": BytesIO(altered_content)
    }
    
    # Act
    downloaded_content = minio_test_client.download_file(minio_path)
    downloaded_checksum = hashlib.sha256(downloaded_content).hexdigest()
    original_checksum = hashlib.sha256(sample_file_bytes).hexdigest()
    
    # Assert
    assert downloaded_checksum != original_checksum
    assert downloaded_content == altered_content 