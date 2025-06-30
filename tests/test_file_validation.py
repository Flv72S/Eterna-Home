"""
Test per la validazione avanzata degli input.
Verifica protezione contro path traversal, file spoofing, MIME mismatch, payload non validi.
"""

import pytest
import os
import tempfile
from fastapi import UploadFile, HTTPException
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import BytesIO
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.models.enums import UserRole
from app.core.security import create_access_token
from app.database import get_db
from app.services.file_validation import FileValidationService
from app.security.validators import sanitize_filename
import io
import json

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
def file_validation_service():
    """Create file validation service"""
    return FileValidationService()

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

def test_valid_pdf_file(file_validation_service):
    """Test validation of valid PDF file"""
    
    # Create valid PDF content (minimal PDF structure)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n trailer\n<<\n/Root 1 0 R\n/Size 3\n>>\nstartxref\n108\n%%EOF"
    
    # Test validation
    result = file_validation_service.validate_file(
        filename="test.pdf",
        content=pdf_content,
        mime_type="application/pdf"
    )
    
    assert result["valid"] == True
    assert result["file_type"] == "pdf"
    assert result["mime_type"] == "application/pdf"

def test_valid_image_file(file_validation_service):
    """Test validation of valid image file"""
    
    # Create minimal PNG content
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178\x00\x00\x00\x00IEND\xaeB`\x82"
    
    # Test validation
    result = file_validation_service.validate_file(
        filename="test.png",
        content=png_content,
        mime_type="image/png"
    )
    
    assert result["valid"] == True
    assert result["file_type"] == "png"
    assert result["mime_type"] == "image/png"

def test_invalid_file_type(file_validation_service):
    """Test validation of invalid file type"""
    
    # Create executable content
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x0e\x1f\xba\x0e\x00\xb4\t\xcd!\xb8\x01L\xcd!This program cannot be run in DOS mode.\r\r\n$"
    
    # Test validation
    result = file_validation_service.validate_file(
        filename="malicious.exe",
        content=exe_content,
        mime_type="application/x-msdownload"
    )
    
    assert result["valid"] == False
    assert "executable" in result["error"].lower()

def test_file_size_limit(file_validation_service):
    """Test file size limit validation"""
    
    # Create large file content (exceeds 100MB limit)
    large_content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    
    # Test validation
    result = file_validation_service.validate_file(
        filename="large_file.pdf",
        content=large_content,
        mime_type="application/pdf"
    )
    
    assert result["valid"] == False
    assert "size" in result["error"].lower()

def test_filename_sanitization():
    """Test filename sanitization"""
    
    # Test various problematic filenames
    test_cases = [
        ("../../../malicious.pdf", "malicious.pdf"),
        ("file<script>.pdf", "filescript.pdf"),
        ("file with spaces.pdf", "file_with_spaces.pdf"),
        ("file@#$%^&*.pdf", "file.pdf"),
        ("file..pdf", "file.pdf"),
        ("file.pdf.exe", "file.pdf.exe"),  # Should be rejected by type validation
        ("file.PDF", "file.pdf"),  # Normalize extension
        ("file.pdf.", "file.pdf"),
        ("", "unnamed_file"),
        ("a" * 300 + ".pdf", "a" * 255 + ".pdf"),  # Truncate long names
    ]
    
    for input_name, expected_output in test_cases:
        sanitized = sanitize_filename(input_name)
        assert sanitized == expected_output

def test_mime_type_validation(file_validation_service):
    """Test MIME type validation"""
    
    # Test valid MIME types
    valid_mime_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/gif",
        "text/plain",
        "application/json",
        "application/xml",
        "text/csv"
    ]
    
    for mime_type in valid_mime_types:
        result = file_validation_service.validate_mime_type(mime_type)
        assert result["valid"] == True
    
    # Test invalid MIME types
    invalid_mime_types = [
        "application/x-msdownload",  # Executable
        "application/x-executable",
        "application/x-shockwave-flash",
        "text/html",  # Potentially dangerous
        "application/javascript"  # Potentially dangerous
    ]
    
    for mime_type in invalid_mime_types:
        result = file_validation_service.validate_mime_type(mime_type)
        assert result["valid"] == False

def test_file_extension_validation(file_validation_service):
    """Test file extension validation"""
    
    # Test valid extensions
    valid_extensions = [
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".json", ".xml", ".csv"
    ]
    
    for ext in valid_extensions:
        result = file_validation_service.validate_extension(ext)
        assert result["valid"] == True
    
    # Test invalid extensions
    invalid_extensions = [
        ".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".vbs", ".js", ".jar"
    ]
    
    for ext in invalid_extensions:
        result = file_validation_service.validate_extension(ext)
        assert result["valid"] == False

def test_magic_number_validation(file_validation_service):
    """Test magic number validation"""
    
    # Test PDF magic number
    pdf_content = b"%PDF-1.4\n"
    result = file_validation_service.validate_magic_number(pdf_content, "application/pdf")
    assert result["valid"] == True
    
    # Test PNG magic number
    png_content = b"\x89PNG\r\n\x1a\n"
    result = file_validation_service.validate_magic_number(png_content, "image/png")
    assert result["valid"] == True
    
    # Test mismatch
    result = file_validation_service.validate_magic_number(pdf_content, "image/png")
    assert result["valid"] == False

def test_content_scanning(file_validation_service):
    """Test content scanning for malicious patterns"""
    
    # Test clean content
    clean_content = b"This is a clean PDF document with normal content."
    result = file_validation_service.scan_content(clean_content)
    assert result["clean"] == True
    
    # Test malicious content patterns
    malicious_patterns = [
        b"<script>alert('xss')</script>",
        b"javascript:alert('xss')",
        b"eval(",
        b"document.cookie",
        b"../",
        b"\\..\\",
        b"cmd.exe",
        b"/bin/bash"
    ]
    
    for pattern in malicious_patterns:
        result = file_validation_service.scan_content(pattern)
        assert result["clean"] == False
        assert "malicious" in result["threats"]

def test_comprehensive_file_validation(file_validation_service):
    """Test comprehensive file validation"""
    
    # Valid file
    valid_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    result = file_validation_service.validate_file_comprehensive(
        filename="document.pdf",
        content=valid_pdf,
        mime_type="application/pdf",
        max_size=1024 * 1024  # 1MB
    )
    
    assert result["valid"] == True
    assert result["file_type"] == "pdf"
    assert result["size_bytes"] == len(valid_pdf)
    
    # Invalid file (executable)
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00"
    
    result = file_validation_service.validate_file_comprehensive(
        filename="malicious.exe",
        content=exe_content,
        mime_type="application/x-msdownload",
        max_size=1024 * 1024
    )
    
    assert result["valid"] == False
    assert len(result["errors"]) > 0

def test_file_upload_validation_endpoint(test_user):
    """Test file upload validation endpoint"""
    
    # Create access token
    token = create_access_token(data={
        "sub": test_user.email,
        "tenant_id": "house_1"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create valid PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    file_data = io.BytesIO(pdf_content)
    
    # Test validation endpoint
    response = client.post(
        "/api/v1/validation/file",
        files={"file": ("test.pdf", file_data, "application/pdf")},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == True

def test_file_validation_error_handling(file_validation_service):
    """Test file validation error handling"""
    
    # Test with empty content
    result = file_validation_service.validate_file(
        filename="empty.pdf",
        content=b"",
        mime_type="application/pdf"
    )
    
    assert result["valid"] == False
    assert "empty" in result["error"].lower()
    
    # Test with None content
    result = file_validation_service.validate_file(
        filename="none.pdf",
        content=None,
        mime_type="application/pdf"
    )
    
    assert result["valid"] == False
    assert "content" in result["error"].lower()

def test_file_validation_performance(file_validation_service):
    """Test file validation performance"""
    
    import time
    
    # Create large but valid file
    large_content = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024)  # 10MB
    
    start_time = time.time()
    result = file_validation_service.validate_file(
        filename="large.pdf",
        content=large_content,
        mime_type="application/pdf"
    )
    end_time = time.time()
    
    # Should complete within reasonable time (less than 5 seconds)
    assert end_time - start_time < 5
    assert result["valid"] == True

def test_file_validation_logging(file_validation_service):
    """Test file validation logging"""
    
    # Test logging of validation attempts
    with patch('app.core.logging_config.get_logger') as mock_logger:
        logger = MagicMock()
        mock_logger.return_value = logger
        
        result = file_validation_service.validate_file(
            filename="test.pdf",
            content=b"%PDF-1.4\n",
            mime_type="application/pdf"
        )
        
        # Verify logging was called
        logger.info.assert_called()
        
        # Verify log contains validation info
        log_call = logger.info.call_args[1]
        assert "file_validation" in log_call.get("event", "")
        assert log_call.get("status") == "success"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 