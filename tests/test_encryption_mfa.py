"""
Test standalone per crittografia e MFA.
Non richiede database o FastAPI.
"""
import pytest
from app.security.encryption import encryption_service
from app.services.mfa_service import mfa_service
from app.models.user import User
import uuid

# Test crittografia
def test_encryption_service():
    """Test del servizio di crittografia."""
    tenant_id = str(uuid.uuid4())
    test_content = b"Test content for encryption"
    
    # Test cifratura
    encrypted_content, nonce = encryption_service.encrypt_file(test_content, tenant_id)
    assert encrypted_content != test_content
    assert len(encrypted_content) > len(test_content)
    
    # Test decifratura
    decrypted_content = encryption_service.decrypt_file(encrypted_content, tenant_id)
    assert decrypted_content == test_content
    
    # Test path cifrato
    encrypted_path = encryption_service.generate_encrypted_path(tenant_id, "test.pdf")
    assert "encrypted" in encrypted_path
    assert ".bin" in encrypted_path
    
    # Test verifica file cifrato
    assert encryption_service.is_encrypted_file(encrypted_path)
    assert not encryption_service.is_encrypted_file("normal/path/file.txt")

def test_encryption_different_tenants():
    """Test che tenant diversi abbiano chiavi diverse."""
    tenant1 = str(uuid.uuid4())
    tenant2 = str(uuid.uuid4())
    test_content = b"Test content"
    
    # Cifra con tenant1
    encrypted1, _ = encryption_service.encrypt_file(test_content, tenant1)
    
    # Cifra con tenant2
    encrypted2, _ = encryption_service.encrypt_file(test_content, tenant2)
    
    # I contenuti cifrati devono essere diversi
    assert encrypted1 != encrypted2
    
    # Decifra correttamente
    decrypted1 = encryption_service.decrypt_file(encrypted1, tenant1)
    decrypted2 = encryption_service.decrypt_file(encrypted2, tenant2)
    
    assert decrypted1 == test_content
    assert decrypted2 == test_content

def test_encryption_invalid_key():
    """Test decifratura con chiave errata."""
    tenant1 = str(uuid.uuid4())
    tenant2 = str(uuid.uuid4())
    test_content = b"Test content"
    
    # Cifra con tenant1
    encrypted, _ = encryption_service.encrypt_file(test_content, tenant1)
    
    # Prova a decifrare con tenant2 (chiave diversa)
    with pytest.raises(Exception):
        encryption_service.decrypt_file(encrypted, tenant2)

# Test MFA
def create_test_user():
    """Crea un utente di test per i test MFA."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        tenant_id=uuid.uuid4(),
        mfa_enabled=False,
        mfa_secret=None
    )

def test_mfa_service():
    """Test del servizio MFA."""
    user = create_test_user()
    
    # Test generazione segreto
    secret = mfa_service.generate_mfa_secret(user)
    assert len(secret) > 0
    assert isinstance(secret, str)
    
    # Test generazione QR code
    qr_code = mfa_service.generate_qr_code(user, secret)
    assert qr_code.startswith("data:image/png;base64,")
    
    # Test setup MFA
    setup_data = mfa_service.setup_mfa(user)
    assert "secret" in setup_data
    assert "qr_code" in setup_data
    assert "backup_codes" in setup_data
    assert len(setup_data["backup_codes"]) == 8

def test_mfa_verification():
    """Test verifica codice TOTP."""
    user = create_test_user()
    secret = mfa_service.generate_mfa_secret(user)
    
    # Genera un codice TOTP valido
    import pyotp
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Test verifica codice valido
    assert mfa_service.verify_totp_code(secret, valid_code)
    
    # Test verifica codice non valido
    assert not mfa_service.verify_totp_code(secret, "000000")

def test_mfa_enable_disable():
    """Test abilitazione/disabilitazione MFA."""
    user = create_test_user()
    
    # Setup MFA
    setup_data = mfa_service.setup_mfa(user)
    secret = setup_data["secret"]
    
    # Genera codice valido
    import pyotp
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    # Test abilitazione
    user.mfa_secret = secret
    success = mfa_service.enable_mfa(user, secret, valid_code)
    assert success
    assert user.mfa_enabled
    
    # Test disabilitazione
    valid_code = totp.now()  # Nuovo codice
    success = mfa_service.disable_mfa(user, valid_code)
    assert success
    assert not user.mfa_enabled

def test_mfa_login_verification():
    """Test verifica MFA durante login."""
    user = create_test_user()
    user.mfa_enabled = True
    user.mfa_secret = mfa_service.generate_mfa_secret(user)
    
    # Genera codice valido
    import pyotp
    totp = pyotp.TOTP(user.mfa_secret)
    valid_code = totp.now()
    
    # Test verifica login
    assert mfa_service.verify_login_mfa(user, valid_code)
    assert not mfa_service.verify_login_mfa(user, "000000")

if __name__ == "__main__":
    # Esegui i test
    pytest.main([__file__, "-v"]) 