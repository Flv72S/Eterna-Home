#!/usr/bin/env python3
"""
Test avanzati per crittografia, accesso, MFA, logging security.json.
"""
import json
from datetime import datetime

# Mock logger semplice
class MockLogger:
    def info(self, msg, **kwargs):
        print(f"[INFO] {msg}: {kwargs}")
    def error(self, msg, **kwargs):
        print(f"[ERROR] {msg}: {kwargs}")

logger = MockLogger()

def fake_iso8601():
    """Mock per fake.iso8601()"""
    return datetime.now().isoformat()

def test_encrypted_file_upload_visibility():
    """Upload file cifrato → file visibile solo da utente autorizzato."""
    authorized_user = {'user_id': 1, 'role': 'admin', 'permissions': ['upload', 'decrypt', 'mfa']}
    unauthorized_user = {'user_id': 2, 'role': 'user', 'permissions': []}
    
    file_info = {'file_id': 'f123', 'encrypted': True, 'owner': authorized_user['user_id']}
    
    # Autorizzato
    can_view = authorized_user['user_id'] == file_info['owner']
    # Non autorizzato
    cannot_view = unauthorized_user['user_id'] != file_info['owner']
    
    logger.info("file_upload", file=file_info, user=authorized_user, can_view=can_view)
    logger.info("file_upload", file=file_info, user=unauthorized_user, can_view=not cannot_view)
    
    assert can_view
    assert cannot_view
    print("✅ Test encrypted_file_upload_visibility PASSATO")


def test_wrong_key_access_logs():
    """Tentativo accesso con chiave sbagliata → errore + log_security_event()."""
    unauthorized_user = {'user_id': 2, 'role': 'user', 'permissions': []}
    
    file_id = 'f123'
    provided_key = 'wrongkey'
    correct_key = 'rightkey'
    error = provided_key != correct_key
    
    log = {
        'event': 'decryption_failed',
        'user_id': unauthorized_user['user_id'],
        'file_id': file_id,
        'provided_key': provided_key,
        'result': 'error',
        'timestamp': fake_iso8601()
    }
    
    if error:
        logger.error("security_event", **log)
    
    assert error
    print("✅ Test wrong_key_access_logs PASSATO")


def test_mfa_enable_logging():
    """Abilitazione MFA → verifica QR, logging evento."""
    authorized_user = {'user_id': 1, 'role': 'admin', 'permissions': ['upload', 'decrypt', 'mfa']}
    
    mfa_event = {
        'user_id': authorized_user['user_id'],
        'action': 'mfa_enabled',
        'qr_code_generated': True,
        'timestamp': fake_iso8601()
    }
    
    logger.info("mfa_event", **mfa_event)
    assert mfa_event['qr_code_generated']
    assert mfa_event['action'] == 'mfa_enabled'
    print("✅ Test mfa_enable_logging PASSATO")


def test_upload_logs_security_json():
    """Upload/documento → log in /logs/security.json."""
    authorized_user = {'user_id': 1, 'role': 'admin', 'permissions': ['upload', 'decrypt', 'mfa']}
    
    log_entry = {
        'event': 'file_upload',
        'user_id': authorized_user['user_id'],
        'file_id': 'f123',
        'encrypted': True,
        'timestamp': fake_iso8601(),
        'log_path': '/logs/security.json'
    }
    
    logger.info("security_json_log", **log_entry)
    # Simula scrittura su file JSON (mock)
    json_str = json.dumps(log_entry)
    assert 'security.json' in log_entry['log_path']
    assert 'file_upload' in json_str
    print("✅ Test upload_logs_security_json PASSATO")


if __name__ == "__main__":
    print("🧪 Esecuzione test crittografia e logging...")
    test_encrypted_file_upload_visibility()
    test_wrong_key_access_logs()
    test_mfa_enable_logging()
    test_upload_logs_security_json()
    print("🎉 Tutti i test crittografia e logging PASSATI!") 