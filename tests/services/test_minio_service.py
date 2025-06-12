import pytest
from unittest.mock import Mock, patch, MagicMock
from minio.error import S3Error
from app.services.minio_service import MinioService

@pytest.fixture
def sample_file_bytes():
    return b"test file content"

@pytest.fixture
def mock_minio_client():
    with patch('minio.Minio') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def minio_service(mock_minio_client):
    with patch.dict('os.environ', {
        'MINIO_ENDPOINT': 'localhost:9000',
        'MINIO_ACCESS_KEY': 'test-key',
        'MINIO_SECRET_KEY': 'test-secret',
        'MINIO_SECURE': 'false',
        'MINIO_DEFAULT_BUCKET': 'test-bucket'
    }), patch.object(MinioService, '_ensure_bucket_exists', return_value=None):
        service = MinioService()
        return service

@patch("app.services.minio_service.Minio")
def test_upload_file_success(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = None

    minio_service = MinioService()
    result = minio_service.upload_file(b"test", "file.txt", "test-bucket", "folder/")

    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.put_object.assert_called_once()
    put_object_args = mock_client.put_object.call_args[1]
    assert put_object_args["bucket_name"] == "test-bucket"
    assert put_object_args["object_name"].startswith("folder/")
    assert put_object_args["object_name"].endswith("file.txt")
    assert put_object_args["data"] == b"test"
    assert put_object_args["content_type"] == "text/plain"
    assert result.endswith("file.txt")

@patch("app.services.minio_service.Minio")
def test_upload_file_with_default_bucket(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = None

    minio_service = MinioService()
    result = minio_service.upload_file(b"test", "file.txt")

    mock_client.bucket_exists.assert_called_once_with("default-bucket")
    mock_client.put_object.assert_called_once()
    put_object_args = mock_client.put_object.call_args[1]
    assert put_object_args["bucket_name"] == "default-bucket"
    assert put_object_args["object_name"].endswith("file.txt")
    assert put_object_args["data"] == b"test"
    assert put_object_args["content_type"] == "text/plain"
    assert result.endswith("file.txt")

@patch("app.services.minio_service.Minio")
def test_upload_file_with_auto_path(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = None

    minio_service = MinioService()
    result = minio_service.upload_file(b"test", "file.txt", "test-bucket")

    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.put_object.assert_called_once()
    put_object_args = mock_client.put_object.call_args[1]
    assert put_object_args["bucket_name"] == "test-bucket"
    assert put_object_args["object_name"].endswith("file.txt")
    assert "/" in put_object_args["object_name"]  # Verifica che ci sia un path
    assert put_object_args["data"] == b"test"
    assert put_object_args["content_type"] == "text/plain"
    assert result.endswith("file.txt")

@patch("app.services.minio_service.Minio")
def test_upload_file_content_type_detection(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = None

    # Test con diversi tipi di file
    test_cases = [
        ("test.pdf", "application/pdf"),
        ("test.jpg", "image/jpeg"),
        ("test.png", "image/png"),
        ("test.txt", "text/plain"),
        ("test.unknown", "application/octet-stream")
    ]

    minio_service = MinioService()
    for filename, expected_type in test_cases:
        result = minio_service.upload_file(b"test", filename, "test-bucket", "folder/")
        
        put_object_args = mock_client.put_object.call_args[1]
        assert put_object_args["content_type"] == expected_type
        assert result.endswith(filename)

@patch("app.services.minio_service.Minio")
def test_upload_file_error_handling(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.side_effect = S3Error("err", "msg", "req", "host")

    minio_service = MinioService()
    with pytest.raises(S3Error) as exc_info:
        minio_service.upload_file(b"test", "file.txt", "test-bucket", "folder/")
    
    assert str(exc_info.value) == "err"
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.put_object.assert_called_once()

@patch("app.services.minio_service.Minio")
def test_bucket_creation(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = False
    mock_client.make_bucket.return_value = None
    mock_client.put_object.return_value = None

    minio_service = MinioService()
    result = minio_service.upload_file(b"test", "file.txt", "test-bucket", "folder/")

    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.make_bucket.assert_called_once_with("test-bucket")
    mock_client.put_object.assert_called_once()
    put_object_args = mock_client.put_object.call_args[1]
    assert put_object_args["bucket_name"] == "test-bucket"
    assert put_object_args["object_name"].startswith("folder/")
    assert put_object_args["object_name"].endswith("file.txt")
    assert result.endswith("file.txt")

@patch("app.services.minio_service.Minio")
def test_bucket_exists_check(mock_minio_class):
    mock_client = MagicMock()
    mock_minio_class.return_value = mock_client

    mock_client.bucket_exists.return_value = True
    mock_client.put_object.return_value = None

    minio_service = MinioService()
    result = minio_service.upload_file(b"test", "file.txt", "test-bucket", "folder/")

    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.make_bucket.assert_not_called()  # Verifica che non venga chiamato make_bucket
    mock_client.put_object.assert_called_once()
    put_object_args = mock_client.put_object.call_args[1]
    assert put_object_args["bucket_name"] == "test-bucket"
    assert put_object_args["object_name"].startswith("folder/")
    assert put_object_args["object_name"].endswith("file.txt")
    assert result.endswith("file.txt") 