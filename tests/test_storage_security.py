"""
Test per le misure di sicurezza dello storage MinIO (Macro-step 2).
Verifica bucket privati, sanitizzazione file, path validation e scansione antivirus.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from io import BytesIO
import os

from app.core.storage_utils import (
    sanitize_filename,
    validate_path_security,
    generate_unique_filename,
    is_valid_tenant_path,
    get_tenant_storage_path
)
from app.services.antivirus_service import AntivirusService
from app.services.minio_service import MinIOService


class TestStorageSecurity:
    """Test per le misure di sicurezza dello storage."""
    
    def test_sanitize_filename_basic(self):
        """Test sanitizzazione base dei nomi file."""
        # Test nomi file normali
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("report 2024.docx") == "report_2024.docx"
        assert sanitize_filename("file-name.txt") == "file-name.txt"
        
        # Test caratteri speciali
        assert sanitize_filename("file@#$%.txt") == "file.txt"
        assert sanitize_filename("file with spaces.pdf") == "file_with_spaces.pdf"
        assert sanitize_filename("file___with___underscores.txt") == "file_with_underscores.txt"
    
    def test_sanitize_filename_path_traversal(self):
        """Test blocco path traversal."""
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("../../../etc/passwd")
        
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("file\\..\\..\\windows\\system32\\config")
        
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("file/../secret.txt")
    
    def test_sanitize_filename_dangerous_chars(self):
        """Test rimozione caratteri pericolosi."""
        dangerous_names = [
            "file<script>.txt",
            "file<alert(1)>.pdf",
            "file:colon.txt",
            "file|pipe.txt",
            "file?query.txt",
            "file*wildcard.txt"
        ]
        
        for name in dangerous_names:
            sanitized = sanitize_filename(name)
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert ":" not in sanitized
            assert "|" not in sanitized
            assert "?" not in sanitized
            assert "*" not in sanitized
    
    def test_validate_path_security(self):
        """Test validazione sicurezza path."""
        # Path sicuri
        assert validate_path_security("tenants/123/documents/file.pdf") is True
        assert validate_path_security("tenants/456/houses/789/bim/model.gltf") is True
        
        # Path pericolosi
        assert validate_path_security("tenants/123/../456/documents/file.pdf") is False
        assert validate_path_security("tenants/123//documents/file.pdf") is False
        assert validate_path_security("tenants/123\\documents\\file.pdf") is False
        assert validate_path_security("tenants/123/documents/file<script>.pdf") is False
    
    def test_generate_unique_filename(self):
        """Test generazione nomi file univoci."""
        tenant_id = uuid.uuid4()
        
        # Genera due nomi per lo stesso file
        filename1 = generate_unique_filename("document.pdf", tenant_id)
        filename2 = generate_unique_filename("document.pdf", tenant_id)
        
        # Verifica che siano diversi
        assert filename1 != filename2
        
        # Verifica formato: YYYY_MM_DD__nome_tenant_uuid.ext
        parts1 = filename1.split("__")
        assert len(parts1) == 2
        assert parts1[1].endswith(".pdf")
        
        # Verifica che contenga il tenant_id
        tenant_short = str(tenant_id)[:8]
        assert tenant_short in filename1
    
    def test_get_tenant_storage_path(self):
        """Test generazione path storage multi-tenant."""
        tenant_id = uuid.uuid4()
        path = get_tenant_storage_path("documents", tenant_id, "report.pdf")
        
        # Verifica struttura path
        assert path.startswith(f"tenants/{tenant_id}/documents/")
        assert path.endswith(".pdf")
        
        # Verifica che contenga timestamp e UUID
        assert "__" in path  # Separatore timestamp
    
    def test_is_valid_tenant_path(self):
        """Test validazione appartenenza path al tenant."""
        tenant_id = uuid.uuid4()
        
        # Path validi
        valid_path = f"tenants/{tenant_id}/documents/file.pdf"
        assert is_valid_tenant_path(valid_path, tenant_id) is True
        
        # Path non validi
        other_tenant_id = uuid.uuid4()
        invalid_path = f"tenants/{other_tenant_id}/documents/file.pdf"
        assert is_valid_tenant_path(invalid_path, tenant_id) is False
        
        # Path malformati
        assert is_valid_tenant_path("invalid/path", tenant_id) is False
        assert is_valid_tenant_path("tenants/invalid-uuid/documents/file.pdf", tenant_id) is False


class TestAntivirusService:
    """Test per il servizio antivirus."""
    
    @pytest.fixture
    def antivirus_service(self):
        """Fixture per il servizio antivirus."""
        return AntivirusService()
    
    @pytest.fixture
    def mock_file(self):
        """Fixture per un file di test."""
        content = b"This is a test file content"
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        file.content_type = "text/plain"
        file.file = BytesIO(content)
        return file
    
    @pytest.mark.asyncio
    async def test_antivirus_service_initialization(self, antivirus_service):
        """Test inizializzazione servizio antivirus."""
        # In modalità sviluppo dovrebbe essere disabilitato
        assert antivirus_service.enabled is False
        assert antivirus_service.clamav_host == "localhost"
        assert antivirus_service.clamav_port == 3310
    
    @pytest.mark.asyncio
    async def test_basic_security_checks_clean_file(self, antivirus_service, mock_file):
        """Test controlli base su file pulito."""
        content = b"This is a clean text file"
        is_clean = await antivirus_service._basic_security_checks(mock_file, content)
        assert is_clean is True
    
    @pytest.mark.asyncio
    async def test_basic_security_checks_large_file(self, antivirus_service, mock_file):
        """Test controllo dimensione file."""
        # File troppo grande (100MB + 1 byte)
        large_content = b"x" * (100 * 1024 * 1024 + 1)
        is_clean = await antivirus_service._basic_security_checks(mock_file, large_content)
        assert is_clean is False
    
    @pytest.mark.asyncio
    async def test_basic_security_checks_dangerous_extension(self, antivirus_service):
        """Test controllo estensioni pericolose."""
        dangerous_files = [
            ("script.exe", b"fake exe content"),
            ("malware.bat", b"fake bat content"),
            ("virus.vbs", b"fake vbs content"),
            ("trojan.js", b"fake js content"),
        ]
        
        for filename, content in dangerous_files:
            file = Mock(spec=UploadFile)
            file.filename = filename
            file.content_type = "application/octet-stream"
            
            is_clean = await antivirus_service._basic_security_checks(file, content)
            assert is_clean is False, f"File {filename} dovrebbe essere rifiutato"
    
    @pytest.mark.asyncio
    async def test_basic_security_checks_executable_signature(self, antivirus_service):
        """Test controllo firme eseguibili."""
        # Test firma Windows PE
        pe_content = b"MZ" + b"x" * 100
        file = Mock(spec=UploadFile)
        file.filename = "fake.txt"
        file.content_type = "text/plain"
        
        is_clean = await antivirus_service._basic_security_checks(file, pe_content)
        assert is_clean is False
    
    def test_validate_mime_type(self, antivirus_service):
        """Test validazione MIME type."""
        # Test MIME type corretto
        file = Mock(spec=UploadFile)
        file.filename = "document.pdf"
        file.content_type = "application/pdf"
        
        assert antivirus_service._validate_mime_type(file) is True
        
        # Test MIME type sospetto
        file.content_type = "application/octet-stream"
        assert antivirus_service._validate_mime_type(file) is False
    
    @pytest.mark.asyncio
    async def test_scan_file_clean(self, antivirus_service, mock_file):
        """Test scansione file pulito."""
        content = b"This is a clean file"
        is_clean, results = await antivirus_service.scan_file(mock_file, content)
        
        assert is_clean is True
        assert results["is_clean"] is True
        assert results["threats_found"] == []
        assert results["scan_method"] == "basic_validation"
    
    def test_get_scan_status(self, antivirus_service):
        """Test stato servizio antivirus."""
        status = antivirus_service.get_scan_status()
        
        assert "enabled" in status
        assert "clamav_host" in status
        assert "clamav_port" in status
        assert "status" in status
        assert "last_check" in status


class TestMinIOServiceSecurity:
    """Test per le misure di sicurezza del servizio MinIO."""
    
    @pytest.fixture
    def minio_service(self):
        """Fixture per il servizio MinIO."""
        return MinIOService(initialize_connection=False)
    
    @pytest.fixture
    def mock_upload_file(self):
        """Fixture per un file di upload."""
        content = b"This is a test file"
        file = Mock(spec=UploadFile)
        file.filename = "test_document.pdf"
        file.content_type = "application/pdf"
        file.file = BytesIO(content)
        return file
    
    def test_bucket_private_configuration(self, minio_service):
        """Test configurazione bucket privato."""
        # Verifica che il metodo esista
        assert hasattr(minio_service, '_configure_bucket_private')
        
        # In modalità sviluppo, il client non è inizializzato
        assert minio_service.client is None
    
    @pytest.mark.asyncio
    async def test_upload_file_with_antivirus(self, minio_service, mock_upload_file):
        """Test upload file con scansione antivirus."""
        tenant_id = uuid.uuid4()
        
        # Mock del servizio antivirus
        with patch('app.services.minio_service.get_antivirus_service') as mock_av:
            mock_av_service = Mock()
            mock_av_service.scan_file = AsyncMock(return_value=(True, {
                "is_clean": True,
                "threats_found": [],
                "scan_method": "basic_validation"
            }))
            mock_av.return_value = mock_av_service
            
            # Esegui upload
            result = await minio_service.upload_file(
                file=mock_upload_file,
                folder="documents",
                tenant_id=tenant_id
            )
            
            # Verifica che la scansione sia stata chiamata
            mock_av_service.scan_file.assert_called_once()
            
            # Verifica risultato
            assert result["dev_mode"] is True
            assert result["tenant_id"] == str(tenant_id)
            assert result["folder"] == "documents"
    
    @pytest.mark.asyncio
    async def test_upload_file_antivirus_rejection(self, minio_service, mock_upload_file):
        """Test rifiuto file da antivirus."""
        tenant_id = uuid.uuid4()
        
        # Mock del servizio antivirus che rifiuta il file
        with patch('app.services.minio_service.get_antivirus_service') as mock_av:
            mock_av_service = Mock()
            mock_av_service.scan_file = AsyncMock(return_value=(False, {
                "is_clean": False,
                "threats_found": ["Suspicious file characteristics detected"],
                "scan_method": "basic_validation"
            }))
            mock_av.return_value = mock_av_service
            
            # Verifica che l'upload sia rifiutato
            with pytest.raises(Exception, match="motivi di sicurezza"):
                await minio_service.upload_file(
                    file=mock_upload_file,
                    folder="documents",
                    tenant_id=tenant_id
                )
    
    def test_create_presigned_url_security(self, minio_service):
        """Test sicurezza URL pre-firmati."""
        tenant_id = uuid.uuid4()
        valid_path = f"tenants/{tenant_id}/documents/file.pdf"
        
        # Test URL valido
        url = minio_service.create_presigned_url(valid_path, tenant_id)
        assert url is not None
        
        # Test URL non autorizzato
        other_tenant_id = uuid.uuid4()
        with pytest.raises(Exception, match="Accesso negato"):
            minio_service.create_presigned_url(valid_path, other_tenant_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 