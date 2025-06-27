"""
Test unitari puri per le utility di storage e antivirus.
Non richiedono import di FastAPI, SQLAlchemy o app.main.
"""

import pytest
import uuid
from unittest.mock import Mock
from io import BytesIO

from app.core.storage_utils import (
    sanitize_filename,
    validate_path_security,
    generate_unique_filename,
    is_valid_tenant_path,
    get_tenant_storage_path
)
from app.services.antivirus_service import AntivirusService

class TestStorageUtils:
    def test_sanitize_filename_basic(self):
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("report 2024.docx") == "report_2024.docx"
        assert sanitize_filename("file-name.txt") == "file-name.txt"
        assert sanitize_filename("file@#$%.txt") == "file.txt"
        assert sanitize_filename("file with spaces.pdf") == "file_with_spaces.pdf"
        assert sanitize_filename("file___with___underscores.txt") == "file_with_underscores.txt"

    def test_sanitize_filename_path_traversal(self):
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("../../../etc/passwd")
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("file/../secret.txt")
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_filename("file\\..\\..\\windows\\system32\\config")

    def test_sanitize_filename_dangerous_chars(self):
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
            assert all(c not in sanitized for c in '<>:|?*')

    def test_validate_path_security(self):
        assert validate_path_security("tenants/123/documents/file.pdf") is True
        assert validate_path_security("tenants/456/houses/789/bim/model.gltf") is True
        assert validate_path_security("tenants/123/../456/documents/file.pdf") is False
        assert validate_path_security("tenants/123//documents/file.pdf") is False
        assert validate_path_security("tenants/123\\documents\\file.pdf") is False
        assert validate_path_security("tenants/123/documents/file<script>.pdf") is False

    def test_generate_unique_filename(self):
        tenant_id = uuid.uuid4()
        filename1 = generate_unique_filename("document.pdf", tenant_id)
        filename2 = generate_unique_filename("document.pdf", tenant_id)
        assert filename1 != filename2
        assert filename1.endswith(".pdf")
        assert "__" in filename1
        tenant_short = str(tenant_id)[:8]
        assert tenant_short in filename1

    def test_get_tenant_storage_path(self):
        tenant_id = uuid.uuid4()
        path = get_tenant_storage_path("documents", tenant_id, "report.pdf")
        assert path.startswith(f"tenants/{tenant_id}/documents/")
        assert path.endswith(".pdf")
        assert "__" in path

    def test_is_valid_tenant_path(self):
        tenant_id = uuid.uuid4()
        valid_path = f"tenants/{tenant_id}/documents/file.pdf"
        assert is_valid_tenant_path(valid_path, tenant_id) is True
        other_tenant_id = uuid.uuid4()
        invalid_path = f"tenants/{other_tenant_id}/documents/file.pdf"
        assert is_valid_tenant_path(invalid_path, tenant_id) is False
        assert is_valid_tenant_path("invalid/path", tenant_id) is False
        assert is_valid_tenant_path("tenants/invalid-uuid/documents/file.pdf", tenant_id) is False

class TestAntivirusService:
    @pytest.fixture
    def antivirus_service(self):
        return AntivirusService()

    @pytest.fixture
    def mock_file(self):
        content = b"This is a test file content"
        file = Mock()
        file.filename = "test.txt"
        file.content_type = "text/plain"
        file.file = BytesIO(content)
        return file

    @pytest.mark.asyncio
    async def test_basic_security_checks_clean_file(self, antivirus_service, mock_file):
        content = b"This is a clean text file"
        is_clean = await antivirus_service._basic_security_checks(mock_file, content)
        assert is_clean is True

    @pytest.mark.asyncio
    async def test_basic_security_checks_large_file(self, antivirus_service, mock_file):
        large_content = b"x" * (100 * 1024 * 1024 + 1)
        is_clean = await antivirus_service._basic_security_checks(mock_file, large_content)
        assert is_clean is False

    @pytest.mark.asyncio
    async def test_basic_security_checks_dangerous_extension(self, antivirus_service):
        dangerous_files = [
            ("script.exe", b"fake exe content"),
            ("malware.bat", b"fake bat content"),
            ("virus.vbs", b"fake vbs content"),
            ("trojan.js", b"fake js content"),
        ]
        for filename, content in dangerous_files:
            file = Mock()
            file.filename = filename
            file.content_type = "application/octet-stream"
            is_clean = await antivirus_service._basic_security_checks(file, content)
            assert is_clean is False

    @pytest.mark.asyncio
    async def test_basic_security_checks_executable_signature(self, antivirus_service):
        pe_content = b"MZ" + b"x" * 100
        file = Mock()
        file.filename = "fake.txt"
        file.content_type = "text/plain"
        is_clean = await antivirus_service._basic_security_checks(file, pe_content)
        assert is_clean is False

    def test_validate_mime_type(self, antivirus_service):
        file = Mock()
        file.filename = "document.pdf"
        file.content_type = "application/pdf"
        assert antivirus_service._validate_mime_type(file) is True
        file.content_type = "application/octet-stream"
        assert antivirus_service._validate_mime_type(file) is False

    @pytest.mark.asyncio
    async def test_scan_file_clean(self, antivirus_service, mock_file):
        content = b"This is a clean file"
        is_clean, results = await antivirus_service.scan_file(mock_file, content)
        assert is_clean is True
        assert results["is_clean"] is True
        assert results["threats_found"] == []
        assert results["scan_method"] == "basic_validation"

    def test_get_scan_status(self, antivirus_service):
        status = antivirus_service.get_scan_status()
        assert "enabled" in status
        assert "clamav_host" in status
        assert "clamav_port" in status
        assert "status" in status
        assert "last_check" in status 