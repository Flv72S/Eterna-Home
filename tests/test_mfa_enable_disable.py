import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.core.security import create_access_token
from app.database import get_db
from app.services.mfa_service import MFAService
from unittest.mock import patch, MagicMock
import pyotp
import qrcode
import io

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
        tenant_id="house_1",
        mfa_enabled=False,
        mfa_secret=None,
        backup_codes=[]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def mfa_service():
    """Create MFA service instance"""
    return MFAService()

def test_mfa_setup_generates_qr_code(db_session, test_user):
    """Test MFA setup generates QR code"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup MFA
    response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields
    assert "qr_code" in data
    assert "secret" in data
    assert "backup_codes" in data
    assert len(data["backup_codes"]) == 10  # Should generate 10 backup codes
    
    # Verify QR code is valid base64
    import base64
    try:
        base64.b64decode(data["qr_code"])
        assert True
    except Exception:
        assert False, "QR code should be valid base64"

def test_mfa_enable_with_valid_code(db_session, test_user):
    """Test MFA enable with valid TOTP code"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup MFA first
    setup_response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    assert setup_response.status_code == 200
    setup_data = setup_response.json()
    
    # Generate valid TOTP code
    secret = setup_data["secret"]
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Enable MFA with valid code
    enable_response = client.post(
        "/api/v1/auth/mfa/enable",
        json={
            "code": valid_code,
            "secret": secret
        },
        headers=headers
    )
    
    # Verify response
    assert enable_response.status_code == 200
    data = enable_response.json()
    assert data["mfa_enabled"] == True
    assert data["message"] == "MFA enabled successfully"
    
    # Verify user is updated in database
    db_session.refresh(test_user)
    assert test_user.mfa_enabled == True
    assert test_user.mfa_secret == secret

def test_mfa_enable_with_invalid_code(db_session, test_user):
    """Test MFA enable with invalid TOTP code"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup MFA first
    setup_response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    assert setup_response.status_code == 200
    setup_data = setup_response.json()
    
    # Try to enable with invalid code
    enable_response = client.post(
        "/api/v1/auth/mfa/enable",
        json={
            "code": "000000",  # Invalid code
            "secret": setup_data["secret"]
        },
        headers=headers
    )
    
    # Should be rejected
    assert enable_response.status_code == 400
    data = enable_response.json()
    assert "invalid" in data["detail"].lower()

def test_mfa_disable(db_session, test_user):
    """Test MFA disable"""
    
    # Enable MFA first
    test_user.mfa_enabled = True
    test_user.mfa_secret = "test_secret"
    test_user.backup_codes = ["backup1", "backup2"]
    db_session.commit()
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Disable MFA
    response = client.post(
        "/api/v1/auth/mfa/disable",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["mfa_enabled"] == False
    assert data["message"] == "MFA disabled successfully"
    
    # Verify user is updated in database
    db_session.refresh(test_user)
    assert test_user.mfa_enabled == False
    assert test_user.mfa_secret is None
    assert test_user.backup_codes == []

def test_mfa_verify_with_valid_code(db_session, test_user):
    """Test MFA verification with valid code"""
    
    # Enable MFA first
    secret = pyotp.random_base32()
    test_user.mfa_enabled = True
    test_user.mfa_secret = secret
    db_session.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Verify MFA
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": valid_code}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True

def test_mfa_verify_with_backup_code(db_session, test_user):
    """Test MFA verification with backup code"""
    
    # Enable MFA with backup codes
    backup_codes = ["backup1", "backup2", "backup3"]
    test_user.mfa_enabled = True
    test_user.mfa_secret = "test_secret"
    test_user.backup_codes = backup_codes
    db_session.commit()
    
    # Verify with backup code
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": "backup1"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True
    
    # Verify backup code is consumed
    db_session.refresh(test_user)
    assert "backup1" not in test_user.backup_codes

def test_mfa_verify_with_invalid_code(db_session, test_user):
    """Test MFA verification with invalid code"""
    
    # Enable MFA
    test_user.mfa_enabled = True
    test_user.mfa_secret = "test_secret"
    db_session.commit()
    
    # Verify with invalid code
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": "000000"}
    )
    
    # Should be rejected
    assert response.status_code == 400
    data = response.json()
    assert data["valid"] == False

def test_mfa_qr_code_content(db_session, test_user):
    """Test QR code contains correct information"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup MFA
    response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Decode QR code
    import base64
    qr_data = base64.b64decode(data["qr_code"])
    
    # QR code should contain otpauth URL
    qr_content = qr_data.decode('utf-8', errors='ignore')
    assert "otpauth://" in qr_content
    assert test_user.email in qr_content

def test_mfa_backup_codes_generation(db_session, test_user):
    """Test backup codes generation"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup MFA
    response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify backup codes
    backup_codes = data["backup_codes"]
    assert len(backup_codes) == 10
    
    # Verify codes are unique
    assert len(set(backup_codes)) == 10
    
    # Verify codes are alphanumeric
    for code in backup_codes:
        assert code.isalnum()
        assert len(code) >= 8  # Should be at least 8 characters

def test_mfa_requires_authentication(db_session, test_user):
    """Test MFA endpoints require authentication"""
    
    # Try to setup MFA without token
    response = client.post("/api/v1/auth/mfa/setup")
    assert response.status_code == 401
    
    # Try to enable MFA without token
    response = client.post("/api/v1/auth/mfa/enable", json={"code": "123456"})
    assert response.status_code == 401
    
    # Try to disable MFA without token
    response = client.post("/api/v1/auth/mfa/disable")
    assert response.status_code == 401

def test_mfa_already_enabled(db_session, test_user):
    """Test MFA setup when already enabled"""
    
    # Enable MFA first
    test_user.mfa_enabled = True
    test_user.mfa_secret = "test_secret"
    db_session.commit()
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to setup MFA again
    response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    
    # Should be rejected
    assert response.status_code == 400
    data = response.json()
    assert "already enabled" in data["detail"].lower()

def test_mfa_not_enabled_operations(db_session, test_user):
    """Test MFA operations when not enabled"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to disable MFA when not enabled
    response = client.post(
        "/api/v1/auth/mfa/disable",
        headers=headers
    )
    
    # Should be rejected
    assert response.status_code == 400
    data = response.json()
    assert "not enabled" in data["detail"].lower()

def test_mfa_secret_rotation(db_session, test_user):
    """Test MFA secret rotation"""
    
    # Enable MFA first
    test_user.mfa_enabled = True
    test_user.mfa_secret = "old_secret"
    db_session.commit()
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup new MFA (should rotate secret)
    response = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify new secret is different
    assert data["secret"] != "old_secret"
    
    # Verify user is updated
    db_session.refresh(test_user)
    assert test_user.mfa_secret == data["secret"] 