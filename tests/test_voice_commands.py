import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.audio_log import AudioLog
from app.core.security import create_access_token
from app.database import get_db
from unittest.mock import patch, MagicMock, AsyncMock
import io
import json
from app.models.enums import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id="house_1"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_house(db_session):
    """Create test house"""
    house = House(
        name="Test House",
        address="Via Test 1",
        tenant_id="house_1"
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    with patch('app.workers.voice_worker.process_voice_command.delay') as mock:
        mock.return_value = MagicMock(id='test-task-id')
        yield mock

def test_voice_command_upload_success(db_session, test_user, test_house, mock_celery_task):
    """Test successful voice command upload"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test audio file
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    # Upload voice command
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general",
            "language": "it-IT"
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message"] == "Voice command received and processing started"
    assert "task_id" in data
    
    # Verify Celery task was called
    mock_celery_task.assert_called_once()

def test_voice_command_without_authentication(db_session, test_house):
    """Test voice command without authentication"""
    
    # Create test audio file
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    # Upload voice command without token
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general"
        }
    )
    
    # Should be rejected
    assert response.status_code == 401  # Unauthorized

def test_voice_command_invalid_file_type(db_session, test_user, test_house):
    """Test voice command with invalid file type"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create invalid file
    invalid_content = b"not audio data"
    invalid_file = io.BytesIO(invalid_content)
    
    # Upload invalid file
    response = client.post(
        "/voice/commands",
        files={"audio": ("test.txt", invalid_file, "text/plain")},
        data={
            "house_id": test_house.id,
            "command_type": "general"
        },
        headers=headers
    )
    
    # Should be rejected
    assert response.status_code == 400  # Bad Request

def test_voice_command_file_size_limit(db_session, test_user, test_house):
    """Test voice command file size limit"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create large audio file
    large_content = b"x" * (50 * 1024 * 1024 + 1)  # 50MB + 1 byte
    large_file = io.BytesIO(large_content)
    
    # Upload large file
    response = client.post(
        "/voice/commands",
        files={"audio": ("large_command.wav", large_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general"
        },
        headers=headers
    )
    
    # Should be rejected due to size
    assert response.status_code == 413  # Payload Too Large

def test_voice_command_worker_activation(db_session, test_user, test_house, mock_celery_task):
    """Test that voice command activates worker correctly"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test audio file
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    # Upload voice command
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "lighting",
            "language": "it-IT"
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    
    # Verify worker was called with correct parameters
    mock_celery_task.assert_called_once()
    call_args = mock_celery_task.call_args[0]  # Positional arguments
    
    # Verify the worker received the correct data
    # This would depend on the actual worker signature
    assert len(call_args) > 0

def test_voice_command_different_types(db_session, test_user, test_house, mock_celery_task):
    """Test different voice command types"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    command_types = ["general", "lighting", "climate", "security", "entertainment"]
    
    for cmd_type in command_types:
        # Create test audio file
        audio_content = b"fake audio data"
        audio_file = io.BytesIO(audio_content)
        
        # Upload voice command
        response = client.post(
            "/voice/commands",
            files={"audio": (f"test_{cmd_type}.wav", audio_file, "audio/wav")},
            data={
                "house_id": test_house.id,
                "command_type": cmd_type,
                "language": "it-IT"
            },
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        
        # Verify worker was called
        mock_celery_task.assert_called()

def test_voice_command_language_support(db_session, test_user, test_house, mock_celery_task):
    """Test voice command language support"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    languages = ["it-IT", "en-US", "de-DE", "fr-FR", "es-ES"]
    
    for language in languages:
        # Create test audio file
        audio_content = b"fake audio data"
        audio_file = io.BytesIO(audio_content)
        
        # Upload voice command
        response = client.post(
            "/voice/commands",
            files={"audio": (f"test_{language}.wav", audio_file, "audio/wav")},
            data={
                "house_id": test_house.id,
                "command_type": "general",
                "language": language
            },
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"

def test_voice_command_tenant_isolation(db_session, test_user, test_house, mock_celery_task):
    """Test voice command tenant isolation"""
    
    # Create access token for specific tenant
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test audio file
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    # Upload voice command
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general",
            "language": "it-IT"
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 202
    data = response.json()
    
    # Verify worker was called with tenant context
    mock_celery_task.assert_called_once()
    
    # The worker should receive tenant information
    # This would be verified in the actual worker implementation

def test_voice_command_audio_log_creation(db_session, test_user, test_house, mock_celery_task):
    """Test that voice command creates audio log entry"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test audio file
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    # Upload voice command
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general",
            "language": "it-IT"
        },
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 202
    
    # Verify audio log was created
    audio_logs = db_session.query(AudioLog).filter(
        AudioLog.user_id == test_user.id,
        AudioLog.house_id == test_house.id
    ).all()
    
    # Should have at least one audio log entry
    assert len(audio_logs) >= 1
    
    # Verify audio log fields
    latest_log = audio_logs[-1]
    assert latest_log.tenant_id == "house_1"
    assert latest_log.house_id == test_house.id
    assert latest_log.user_id == test_user.id
    assert latest_log.command_type == "general"
    assert latest_log.language == "it-IT"

def test_voice_command_error_handling(db_session, test_user, test_house):
    """Test voice command error handling"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with missing required fields
    response = client.post(
        "/voice/commands",
        files={"audio": ("test.wav", io.BytesIO(b"data"), "audio/wav")},
        data={},  # Missing house_id
        headers=headers
    )
    
    # Should return error
    assert response.status_code == 422  # Unprocessable Entity

def test_voice_command_task_status(db_session, test_user, test_house, mock_celery_task):
    """Test voice command task status endpoint"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload voice command to get task_id
    audio_content = b"fake audio data"
    audio_file = io.BytesIO(audio_content)
    
    response = client.post(
        "/voice/commands",
        files={"audio": ("test_command.wav", audio_file, "audio/wav")},
        data={
            "house_id": test_house.id,
            "command_type": "general"
        },
        headers=headers
    )
    
    assert response.status_code == 202
    data = response.json()
    task_id = data["task_id"]
    
    # Check task status
    status_response = client.get(
        f"/voice/commands/status/{task_id}",
        headers=headers
    )
    
    # Should return task status
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert "status" in status_data 