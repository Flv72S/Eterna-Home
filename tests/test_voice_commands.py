import pytest
import uuid
import io
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.audio_log import AudioLog
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.models.role_permission import RolePermission
from app.core.security import create_access_token
from app.database import get_db
from tests.utils.auth import create_test_user_with_tenant, get_auth_headers

client = TestClient(app)

def create_test_permission(session: Session, name: str, description: str) -> Permission:
    """Crea una permission di test o la recupera se già esistente."""
    permission = session.exec(select(Permission).where(Permission.name == name)).first()
    if permission:
        return permission
    permission = Permission(
        name=name,
        description=description,
        resource="voice_command",
        action="submit",
        is_active=True
    )
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission

def create_test_role(session: Session, name: str, description: str) -> Role:
    """Crea un ruolo di test o lo recupera se già esistente."""
    role = session.exec(select(Role).where(Role.name == name)).first()
    if role:
        return role
    role = Role(
        name=name,
        description=description,
        is_active=True
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

def assign_role_to_user_in_tenant(session: Session, user_id: int, tenant_id: uuid.UUID, role_name: str):
    """Assegna un ruolo a un utente in un tenant specifico."""
    user_tenant_role = UserTenantRole(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role_name,
        is_active=True
    )
    session.add(user_tenant_role)
    session.commit()
    session.refresh(user_tenant_role)
    return user_tenant_role

@pytest.fixture
def session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_user_with_voice_permissions(session):
    """Crea un utente di test con tutti i permessi voice necessari."""
    # Crea utente e tenant
    user, tenant_id = create_test_user_with_tenant(session)
    
    # Crea ruolo editor con permessi voice
    editor_role = create_test_role(session, "editor", "Editor role with voice permissions")
    
    # Crea permessi voice
    permissions = [
        "submit_voice",
        "read_voice_logs",
        "manage_voice_logs"
    ]
    
    for perm_name in permissions:
        permission = create_test_permission(session, perm_name, f"Permission to {perm_name}")
        # Assegna il permesso al ruolo editor
        existing = session.exec(
            select(RolePermission).where(
                RolePermission.role_id == editor_role.id,
                RolePermission.permission_id == permission.id
            )
        ).first()
        if not existing:
            role_permission = RolePermission(
                role_id=editor_role.id,
                permission_id=permission.id
            )
            session.add(role_permission)
    
    # Assegna il ruolo editor all'utente nel tenant
    assign_role_to_user_in_tenant(session, user.id, tenant_id, "editor")
    
    session.commit()
    return user, tenant_id, session

@pytest.fixture
def test_house(test_user_with_voice_permissions):
    """Crea una casa di test per lo stesso tenant dell'utente."""
    user, tenant_id, session = test_user_with_voice_permissions
    
    # Crea una casa di test per lo stesso tenant dell'utente
    house = House(
        name="Test House",
        address="123 Test Street",
        tenant_id=tenant_id,
        owner_id=user.id,
        is_active=True
    )
    session.add(house)
    session.commit()
    session.refresh(house)
    
    yield house

@pytest.fixture
def mock_rabbitmq_manager():
    """Mock per RabbitMQ manager con AsyncMock e contatore chiamate."""
    with patch('app.routers.voice.get_rabbitmq_manager') as mock:
        mock_manager = MagicMock()
        call_counter = {'count': 0}
        async def mock_publish_message(*args, **kwargs):
            call_counter['count'] += 1
            return True
        mock_manager.publish_message = AsyncMock(side_effect=mock_publish_message)
        mock_manager.publish_message.call_counter = call_counter
        mock.return_value = mock_manager
        yield mock_manager

@pytest.fixture
def mock_minio_client():
    """Mock per MinIO client"""
    with patch('app.routers.voice.get_minio_client') as mock:
        mock_client = MagicMock()
        mock_client.upload_file = MagicMock()
        mock.return_value = mock_client
        yield mock_client

def test_voice_command_text_success(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test successful voice command with text"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Test data
    command_data = {
        "transcribed_text": "Accendi le luci del soggiorno",
        "house_id": test_house.id,
        "node_id": None
    }
    
    # Submit voice command
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert data["status"] == "accepted"
    assert data["message"] == "Comando vocale ricevuto e inviato in elaborazione"
    assert "request_id" in data
    
    # Verify RabbitMQ message was sent
    mock_rabbitmq_manager.publish_message.assert_called_once()

def test_voice_command_audio_success(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test voice command con file audio valido"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Mock per MinIO client
    with patch('app.routers.voice.get_minio_client') as mock_minio:
        mock_minio_client = MagicMock()
        mock_minio_client.upload_file = MagicMock()
        mock_minio.return_value = mock_minio_client
        
        # Crea un file WAV minimale valido (44 byte header)
        wav_header = (
            b'RIFF' + (36).to_bytes(4, 'little') + b'WAVEfmt ' +
            (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') +
            (44100).to_bytes(4, 'little') + (44100*2).to_bytes(4, 'little') +
            (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') +
            b'data' + (0).to_bytes(4, 'little')
        )
        audio_file = io.BytesIO(wav_header)
        
        response = client.post(
            "/api/v1/voice/commands/audio",
            files={"audio_file": ("test.wav", audio_file, "audio/wav")},
            data={"house_id": test_house.id},
            headers=headers
        )
        assert response.status_code == 202

def test_voice_command_without_authentication(test_house):
    """Test voice command without authentication"""
    # Test data
    command_data = {
        "transcribed_text": "Accendi le luci",
        "house_id": test_house.id
    }
    
    # Submit voice command without token
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data
    )
    
    # Should be rejected
    assert response.status_code == 401  # Unauthorized

def test_voice_command_invalid_file_type(test_user_with_voice_permissions, test_house):
    """Test voice command con file non audio"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    invalid_content = b"not audio data"
    invalid_file = io.BytesIO(invalid_content)
    
    response = client.post(
        "/api/v1/voice/commands/audio",
        files={"audio_file": ("test.txt", invalid_file, "text/plain")},
        data={"house_id": test_house.id},
        headers=headers
    )
    assert response.status_code == 422  # FastAPI restituisce 422 per errori di validazione

def test_voice_command_file_size_limit(test_user_with_voice_permissions, test_house):
    """Test voice command file size limit"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    large_content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    large_file = io.BytesIO(large_content)
    
    response = client.post(
        "/api/v1/voice/commands/audio",
        files={"audio_file": ("large_command.wav", large_file, "audio/wav")},
        data={"house_id": test_house.id},
        headers=headers
    )
    assert response.status_code == 413

def test_voice_command_worker_activation(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test che il worker viene attivato correttamente"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    command_data = {
        "transcribed_text": "Accendi le luci del soggiorno",
        "house_id": test_house.id
    }
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    assert response.status_code == 202
    # Verifica che publish_message sia stato chiamato
    assert mock_rabbitmq_manager.publish_message.call_counter['count'] == 1

def test_voice_command_different_types(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test different voice command types"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Test different command types
    commands = [
        "Accendi le luci",
        "Imposta la temperatura a 22 gradi",
        "Apri la porta del garage",
        "Chiudi le tapparelle"
    ]
    
    for command in commands:
        command_data = {
            "transcribed_text": command,
            "house_id": test_house.id
        }
        
        response = client.post(
            "/api/v1/voice/commands",
            json=command_data,
            headers=headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"

def test_voice_command_language_support(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test voice command language support"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Test different languages
    commands = [
        "Turn on the lights",  # English
        "Allume les lumières",  # French
        "Enciende las luces",   # Spanish
        "Accendi le luci"       # Italian
    ]
    
    for command in commands:
        command_data = {
            "transcribed_text": command,
            "house_id": test_house.id
        }
        
        response = client.post(
            "/api/v1/voice/commands",
            json=command_data,
            headers=headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"

def test_voice_command_tenant_isolation(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test voice command tenant isolation"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Create another user with different tenant
    other_user, other_tenant_id = create_test_user_with_tenant(session)
    
    # Create house for other tenant
    other_house = House(
        name="Other Test House",
        address="456 Other Street",
        tenant_id=other_tenant_id,
        owner_id=other_user.id,
        is_active=True
    )
    session.add(other_house)
    session.commit()
    session.refresh(other_house)
    
    # Assign the same voice permissions to other user (reuse existing permissions)
    editor_role = session.exec(select(Role).where(Role.name == "editor")).first()
    assign_role_to_user_in_tenant(session, other_user.id, other_tenant_id, "editor")
    session.commit()
    
    other_headers = get_auth_headers(other_user, other_tenant_id)
    
    # Submit command with first user
    command_data = {
        "transcribed_text": "Comando del primo utente",
        "house_id": test_house.id
    }
    
    response1 = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    
    assert response1.status_code == 202
    
    # Submit command with second user (should be isolated)
    command_data2 = {
        "transcribed_text": "Comando del secondo utente",
        "house_id": other_house.id
    }
    
    response2 = client.post(
        "/api/v1/voice/commands",
        json=command_data2,
        headers=other_headers
    )
    
    assert response2.status_code == 202
    
    # Verify both commands were processed
    assert mock_rabbitmq_manager.publish_message.call_counter['count'] == 2

def test_voice_command_audio_log_creation(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test that voice command creates audio log correctly"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Submit voice command
    command_data = {
        "transcribed_text": "Test audio log creation",
        "house_id": test_house.id
    }
    
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    
    assert response.status_code == 202
    
    # Verify audio log was created in database
    audio_logs = session.exec(select(AudioLog).where(AudioLog.user_id == user.id)).all()
    assert len(audio_logs) > 0
    
    latest_log = audio_logs[-1]
    assert latest_log.transcribed_text == "Test audio log creation"
    assert latest_log.house_id == test_house.id
    assert latest_log.tenant_id == tenant_id
    assert latest_log.processing_status == "received"

def test_voice_command_error_handling(test_user_with_voice_permissions, test_house):
    """Test voice command error handling"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Test with empty transcribed text
    command_data = {
        "transcribed_text": "",
        "house_id": test_house.id
    }
    
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    
    # Should be rejected
    assert response.status_code == 422  # Unprocessable Entity

def test_voice_command_task_status(test_user_with_voice_permissions, test_house, mock_rabbitmq_manager):
    """Test voice command task status"""
    user, tenant_id, session = test_user_with_voice_permissions
    headers = get_auth_headers(user, tenant_id)
    
    # Submit voice command
    command_data = {
        "transcribed_text": "Check task status",
        "house_id": test_house.id
    }
    
    response = client.post(
        "/api/v1/voice/commands",
        json=command_data,
        headers=headers
    )
    
    assert response.status_code == 202
    data = response.json()
    
    # Verify request_id format
    assert data["request_id"].startswith("audiolog-")
    
    # Extract audiolog_id from request_id
    audiolog_id = data["request_id"].split("-")[1]
    
    # Verify audio log exists with correct status
    audio_log = session.get(AudioLog, int(audiolog_id))
    assert audio_log is not None
    assert audio_log.processing_status == "received"
    assert audio_log.user_id == user.id
    assert audio_log.tenant_id == tenant_id 