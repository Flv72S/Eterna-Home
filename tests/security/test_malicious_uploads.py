"""
Test per la protezione contro upload di contenuti malevoli in Eterna Home.
Verifica che file pericolosi, MIME types non validi e contenuti malevoli siano rifiutati.
"""

import pytest
import io
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_tenant_role import UserTenantRole
from app.core.security import create_access_token
from app.database import get_db
from app.models.enums import UserRole

client = TestClient(app)

@pytest.fixture
def db_session():
    """Get database session for testing"""
    with next(get_db()) as session:
        yield session

@pytest.fixture
def test_tenant_id():
    """Create a test tenant ID"""
    return uuid.uuid4()

@pytest.fixture
def test_user(db_session, test_tenant_id):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        tenant_id=test_tenant_id,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_house(db_session, test_tenant_id, test_user):
    """Create test house"""
    house = House(
        name="Test House",
        address="Via Test 1",
        tenant_id=test_tenant_id,
        owner_id=test_user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def setup_rbac(db_session, test_tenant_id, test_user):
    """Setup RBAC permissions"""
    # Create permissions
    permissions = [
        Permission(
            name="read_documents",
            resource="documents",
            action="read",
            is_active=True
        ),
        Permission(
            name="write_documents",
            resource="documents", 
            action="write",
            is_active=True
        )
    ]
    
    for perm in permissions:
        db_session.add(perm)
    db_session.commit()
    
    # Assign admin role to user
    user_role = UserTenantRole(
        user_id=test_user.id,
        tenant_id=test_tenant_id,
        role="admin"
    )
    db_session.add(user_role)
    db_session.commit()

class TestMaliciousUploads:
    """Test suite per la protezione contro upload malevoli"""
    
    def test_upload_executable_file_rejected(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che file eseguibili (.exe, .bat, .sh) siano rifiutati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test various executable files
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload"),
            ("script.bat", b"@echo off\nstart calc.exe", "application/x-bat"),
            ("script.sh", b"#!/bin/bash\necho 'malicious'", "application/x-shellscript"),
            ("script.vbs", b"WScript.Echo 'malicious'", "text/vbscript"),
            ("script.js", b"alert('malicious')", "application/x-javascript"),
            ("script.py", b"import os\nos.system('rm -rf /')", "text/x-python")
        ]
        
        for filename, content, mime_type in malicious_files:
            file_data = io.BytesIO(content)
            
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": (filename, file_data, mime_type)},
                data={
                    "title": f"Test {filename}",
                    "description": "Test malicious file",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should be rejected
            assert response.status_code in [400, 422], f"File {filename} should be rejected"
            
            # Check error message
            error_data = response.json()
            assert "non consentito" in error_data.get("detail", "").lower() or \
                   "forbidden" in error_data.get("detail", "").lower() or \
                   "not allowed" in error_data.get("detail", "").lower()
    
    def test_upload_mime_type_mismatch_rejected(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che file con MIME type non corrispondente all'estensione siano rifiutati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test MIME type mismatches
        mime_mismatches = [
            # File with .jpg extension but PDF content
            ("fake_image.jpg", b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj", "image/jpeg"),
            # File with .pdf extension but executable content
            ("fake_document.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf"),
            # File with .docx extension but HTML content
            ("fake_document.docx", b"<html><body><script>alert('xss')</script></body></html>", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        ]
        
        for filename, content, mime_type in mime_mismatches:
            file_data = io.BytesIO(content)
            
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": (filename, file_data, mime_type)},
                data={
                    "title": f"Test {filename}",
                    "description": "Test MIME mismatch",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should be rejected due to MIME type validation
            assert response.status_code in [400, 422], f"File {filename} with MIME mismatch should be rejected"
    
    def test_upload_path_traversal_filename_rejected(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che filename con path traversal siano rifiutati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test path traversal filenames
        path_traversal_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5C..%5C..%5Cwindows%5Csystem32%5Cconfig%5Csam",
            "normal_file.pdf/../../../etc/passwd",
            "normal_file.pdf\\..\\..\\..\\windows\\system32\\config\\sam"
        ]
        
        safe_content = b"This is safe content"
        
        for filename in path_traversal_filenames:
            file_data = io.BytesIO(safe_content)
            
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": (filename, file_data, "application/pdf")},
                data={
                    "title": f"Test {filename}",
                    "description": "Test path traversal",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should be rejected
            assert response.status_code in [400, 422], f"Filename {filename} should be rejected for path traversal"
            
            # Check error message
            error_data = response.json()
            assert "path traversal" in error_data.get("detail", "").lower() or \
                   "non validi" in error_data.get("detail", "").lower()
    
    def test_upload_unicode_emoji_filename_sanitized(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che filename con Unicode/emoji siano sanificati correttamente"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Unicode and emoji filenames
        unicode_filenames = [
            "document_🚀_test.pdf",
            "file_🎉_🎊_🎈.pdf",
            "test_文件_文档.pdf",
            "document_привет_мир.pdf",
            "file_🌍_world_🌎.pdf"
        ]
        
        safe_content = b"This is safe content"
        
        for filename in unicode_filenames:
            file_data = io.BytesIO(safe_content)
            
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": (filename, file_data, "application/pdf")},
                data={
                    "title": f"Test {filename}",
                    "description": "Test Unicode filename",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should be accepted but sanitized
            assert response.status_code == 200, f"Unicode filename {filename} should be accepted"
            
            # Verify the response contains sanitized filename info
            data = response.json()
            assert "file_url" in data or "storage_path" in data
    
    def test_upload_oversized_file_rejected(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che file troppo grandi siano rifiutati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create oversized content (51MB - over the 50MB limit)
        oversized_content = b"x" * (51 * 1024 * 1024)
        file_data = io.BytesIO(oversized_content)
        
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("oversized_document.pdf", file_data, "application/pdf")},
            data={
                "title": "Test Oversized Document",
                "description": "Test file size limit",
                "document_type": "general",
                "house_id": test_house.id
            },
            headers=headers
        )
        
        # Should be rejected
        assert response.status_code in [400, 413], "Oversized file should be rejected"
        
        # Check error message
        error_data = response.json()
        assert "size" in error_data.get("detail", "").lower() or \
               "limit" in error_data.get("detail", "").lower()
    
    def test_upload_pdf_with_embedded_javascript_detected(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che PDF con JavaScript embedded siano rilevati e loggati"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create PDF content with embedded JavaScript
        pdf_with_js = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
/JavaScript <<
/Names [(EmbeddedJS) 5 0 R]
>>
endstream
endobj

5 0 obj
<<
/Type /JavaScript
/JS (alert('XSS attack'))
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
0000000304 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
400
%%EOF"""
        
        file_data = io.BytesIO(pdf_with_js)
        
        # Mock antivirus service to detect JavaScript
        with patch('app.services.antivirus_service.get_antivirus_service') as mock_antivirus:
            mock_antivirus.return_value.scan_file.return_value = {
                "is_safe": False,
                "threats": ["Embedded JavaScript detected"],
                "scan_result": "MALICIOUS"
            }
            
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("malicious_pdf.pdf", file_data, "application/pdf")},
                data={
                    "title": "Test PDF with JavaScript",
                    "description": "Test JavaScript detection",
                    "document_type": "general",
                    "house_id": test_house.id
                },
                headers=headers
            )
            
            # Should be rejected due to antivirus detection
            assert response.status_code in [400, 422], "PDF with JavaScript should be rejected"
            
            # Verify antivirus was called
            mock_antivirus.return_value.scan_file.assert_called_once()
    
    def test_upload_duplicate_filename_handled(self, db_session, test_user, test_house, setup_rbac, test_tenant_id):
        """Test che filename duplicati generino UUID unici"""
        
        # Create access token
        token = create_access_token(data={
            "sub": test_user.email,
            "tenant_id": str(test_tenant_id)
        })
        headers = {"Authorization": f"Bearer {token}"}
        
        safe_content = b"This is safe content"
        filename = "duplicate_document.pdf"
        
        # Upload first file
        file_data1 = io.BytesIO(safe_content)
        response1 = client.post(
            "/api/v1/documents/upload",
            files={"file": (filename, file_data1, "application/pdf")},
            data={
                "title": "First Document",
                "description": "First upload",
                "document_type": "general",
                "house_id": test_house.id
            },
            headers=headers
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Upload second file with same filename
        file_data2 = io.BytesIO(safe_content)
        response2 = client.post(
            "/api/v1/documents/upload",
            files={"file": (filename, file_data2, "application/pdf")},
            data={
                "title": "Second Document",
                "description": "Second upload",
                "document_type": "general",
                "house_id": test_house.id
            },
            headers=headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify both documents exist with different IDs
        assert data1["id"] != data2["id"]
        
        # Verify storage paths are different (should contain unique identifiers)
        assert data1.get("file_url") != data2.get("file_url") 