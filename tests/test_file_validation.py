"""
Test per la validazione avanzata degli input.
Verifica protezione contro path traversal, file spoofing, MIME mismatch, payload non validi.
"""

import pytest
import os
import tempfile
from fastapi import UploadFile, HTTPException
from unittest.mock import Mock, patch
from io import BytesIO

from app.security.validators import (
    FileValidator, 
    TextValidator,
    sanitize_filename,
    is_allowed_mime_type,
    validate_file_upload,
    validate_text_field
)

class TestFileValidation:
    """Test per la validazione dei file."""
    
    def test_sanitize_filename_valid(self):
        """Test sanificazione nome file valido."""
        filename = "documento_test.pdf"
        result = sanitize_filename(filename)
        assert result == "documento_test.pdf"
    
    def test_sanitize_filename_path_traversal(self):
        """Test rifiuto path traversal."""
        with pytest.raises(HTTPException) as exc_info:
            sanitize_filename("../../../etc/passwd")
        assert exc_info.value.status_code == 422
        assert "path traversal" in exc_info.value.detail.lower()
    
    def test_sanitize_filename_dangerous_chars(self):
        """Test rimozione caratteri pericolosi."""
        filename = "file<>:\"/\\|?*.txt"
        result = sanitize_filename(filename)
        assert result == "file_______.txt"
    
    def test_sanitize_filename_empty(self):
        """Test rifiuto nome file vuoto."""
        with pytest.raises(HTTPException) as exc_info:
            sanitize_filename("")
        assert exc_info.value.status_code == 422
    
    def test_sanitize_filename_too_long(self):
        """Test troncamento nome file troppo lungo."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_is_allowed_mime_type_valid(self):
        """Test MIME type valido."""
        assert is_allowed_mime_type("application/pdf", "document.pdf") == True
        assert is_allowed_mime_type("audio/wav", "audio.wav") == True
    
    def test_is_allowed_mime_type_forbidden(self):
        """Test MIME type vietato."""
        assert is_allowed_mime_type("application/x-msdownload", "file.exe") == False
        assert is_allowed_mime_type("text/x-python", "script.py") == False
    
    def test_is_allowed_mime_type_mismatch(self):
        """Test mismatch tra MIME type e estensione."""
        assert is_allowed_mime_type("application/pdf", "file.exe") == False
    
    def test_validate_file_upload_valid(self):
        """Test upload file valido."""
        # Crea un file mock
        file_content = b"test content"
        file = UploadFile(
            filename="test.pdf",
            content_type="application/pdf",
            file=BytesIO(file_content)
        )
        
        # Mock del metodo read
        with patch.object(file, 'read', return_value=file_content):
            with patch.object(file, 'seek'):
                validate_file_upload(file, ["application/pdf"], 1024 * 1024)
    
    def test_validate_file_upload_invalid_mime(self):
        """Test upload file con MIME type non consentito."""
        file = UploadFile(
            filename="test.exe",
            content_type="application/x-msdownload",
            file=BytesIO(b"test")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file_upload(file, ["application/pdf"], 1024 * 1024)
        assert exc_info.value.status_code == 422
        assert "non consentito" in exc_info.value.detail
    
    def test_validate_file_upload_too_large(self):
        """Test upload file troppo grande."""
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        file = UploadFile(
            filename="large.pdf",
            content_type="application/pdf",
            file=BytesIO(large_content)
        )
        
        with patch.object(file, 'read', return_value=large_content):
            with patch.object(file, 'seek'):
                with pytest.raises(HTTPException) as exc_info:
                    validate_file_upload(file, ["application/pdf"], 10 * 1024 * 1024)
                assert exc_info.value.status_code == 413
    
    def test_validate_file_upload_path_traversal_filename(self):
        """Test upload file con nome contenente path traversal."""
        file = UploadFile(
            filename="../../../etc/passwd",
            content_type="application/pdf",
            file=BytesIO(b"test")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file_upload(file, ["application/pdf"], 1024 * 1024)
        assert exc_info.value.status_code == 422

class TestTextValidation:
    """Test per la validazione dei campi testo."""
    
    def test_validate_text_field_valid(self):
        """Test campo testo valido."""
        result = TextValidator.validate_text_field("Test description", "description", 100)
        assert result == "Test description"
    
    def test_validate_text_field_too_long(self):
        """Test campo testo troppo lungo."""
        long_text = "a" * 101
        with pytest.raises(HTTPException) as exc_info:
            TextValidator.validate_text_field(long_text, "description", 100)
        assert exc_info.value.status_code == 422
        assert "troppo lungo" in exc_info.value.detail
    
    def test_validate_text_field_sql_injection(self):
        """Test rifiuto SQL injection."""
        sql_injection = "'; DROP TABLE users; --"
        with pytest.raises(HTTPException) as exc_info:
            TextValidator.validate_text_field(sql_injection, "description", 1000)
        assert exc_info.value.status_code == 422
        assert "non consentito" in exc_info.value.detail
    
    def test_validate_text_field_emoji(self):
        """Test rifiuto emoji."""
        emoji_text = "Test with emoji 🚀"
        with pytest.raises(HTTPException) as exc_info:
            TextValidator.validate_text_field(emoji_text, "description", 1000)
        assert exc_info.value.status_code == 422
        assert "non consentito" in exc_info.value.detail
    
    def test_validate_text_field_html(self):
        """Test rifiuto HTML."""
        html_text = "Test with <script>alert('xss')</script>"
        with pytest.raises(HTTPException) as exc_info:
            TextValidator.validate_text_field(html_text, "description", 1000)
        assert exc_info.value.status_code == 422
        assert "non consentito" in exc_info.value.detail
    
    def test_validate_text_field_empty(self):
        """Test campo testo vuoto (dovrebbe essere accettato)."""
        result = TextValidator.validate_text_field("", "description", 100)
        assert result == ""
    
    def test_validate_text_field_none(self):
        """Test campo testo None (dovrebbe essere accettato)."""
        result = TextValidator.validate_text_field(None, "description", 100)
        assert result is None

class TestIntegrationValidation:
    """Test di integrazione per scenari reali."""
    
    def test_document_upload_scenario(self):
        """Test scenario completo upload documento."""
        # File valido
        valid_file = UploadFile(
            filename="documento_test.pdf",
            content_type="application/pdf",
            file=BytesIO(b"test content")
        )
        
        with patch.object(valid_file, 'read', return_value=b"test content"):
            with patch.object(valid_file, 'seek'):
                # Dovrebbe passare senza errori
                validate_file_upload(valid_file, ["application/pdf"], 50 * 1024 * 1024)
    
    def test_bim_upload_scenario(self):
        """Test scenario completo upload BIM."""
        # File BIM valido
        bim_file = UploadFile(
            filename="model.ifc",
            content_type="model/ifc",
            file=BytesIO(b"test content")
        )
        
        with patch.object(bim_file, 'read', return_value=b"test content"):
            with patch.object(bim_file, 'seek'):
                # Dovrebbe passare senza errori
                validate_file_upload(bim_file, ["model/ifc"], 500 * 1024 * 1024)
    
    def test_audio_upload_scenario(self):
        """Test scenario completo upload audio."""
        # File audio valido
        audio_file = UploadFile(
            filename="recording.wav",
            content_type="audio/wav",
            file=BytesIO(b"test content")
        )
        
        with patch.object(audio_file, 'read', return_value=b"test content"):
            with patch.object(audio_file, 'seek'):
                # Dovrebbe passare senza errori
                validate_file_upload(audio_file, ["audio/wav"], 100 * 1024 * 1024)
    
    def test_malicious_upload_scenarios(self):
        """Test scenari di upload malevoli."""
        malicious_files = [
            # File eseguibile
            ("malware.exe", "application/x-msdownload", b"test"),
            # Path traversal
            ("../../../etc/passwd", "application/pdf", b"test"),
            # File troppo grande
            ("large.pdf", "application/pdf", b"x" * (100 * 1024 * 1024 + 1)),
            # MIME type sbagliato
            ("script.py", "text/x-python", b"test"),
        ]
        
        for filename, content_type, content in malicious_files:
            file = UploadFile(
                filename=filename,
                content_type=content_type,
                file=BytesIO(content)
            )
            
            with patch.object(file, 'read', return_value=content):
                with patch.object(file, 'seek'):
                    with pytest.raises(HTTPException) as exc_info:
                        validate_file_upload(file, ["application/pdf"], 100 * 1024 * 1024)
                    assert exc_info.value.status_code in [422, 413]
    
    def test_malicious_text_scenarios(self):
        """Test scenari di testo malevolo."""
        malicious_texts = [
            ("SQL injection", "'; DROP TABLE users; --"),
            ("XSS attack", "<script>alert('xss')</script>"),
            ("Emoji", "Test with 🚀"),
            ("JavaScript", "javascript:alert('xss')"),
            ("Too long", "a" * 1001),
        ]
        
        for description, text in malicious_texts:
            with pytest.raises(HTTPException) as exc_info:
                TextValidator.validate_text_field(text, "description", 1000)
            assert exc_info.value.status_code == 422

class TestLoggingValidation:
    """Test per verificare che il logging funzioni correttamente."""
    
    @patch('app.security.validators.multi_tenant_logger')
    def test_logging_invalid_filename(self, mock_logger):
        """Test logging per nome file non valido."""
        with pytest.raises(HTTPException):
            sanitize_filename("../../../etc/passwd")
        
        # Verifica che il logger sia stato chiamato
        mock_logger.log_security_event.assert_called()
    
    @patch('app.security.validators.multi_tenant_logger')
    def test_logging_invalid_upload(self, mock_logger):
        """Test logging per upload non valido."""
        file = UploadFile(
            filename="test.exe",
            content_type="application/x-msdownload",
            file=BytesIO(b"test")
        )
        
        with pytest.raises(HTTPException):
            validate_file_upload(file, ["application/pdf"], 1024 * 1024)
        
        # Verifica che il logger sia stato chiamato
        mock_logger.log_security_event.assert_called()
    
    @patch('app.security.validators.multi_tenant_logger')
    def test_logging_invalid_text(self, mock_logger):
        """Test logging per testo non valido."""
        with pytest.raises(HTTPException):
            TextValidator.validate_text_field("'; DROP TABLE users; --", "description", 1000)
        
        # Verifica che il logger sia stato chiamato
        mock_logger.log_security_event.assert_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 