import pytest
from sqlmodel import select
from app.models.document_version import DocumentVersion
from app.models.document import Document
from app.models.user import User
from app.schemas.document_version import DocumentVersionCreate, DocumentVersionUpdate
from app.crud.document_version import (
    create_document_version,
    get_document_version,
    get_document_versions,
    update_document_version,
    delete_document_version,
    get_document_version_by_version_number
)

def test_create_document_version(db_session, test_user, test_document):
    version_data = DocumentVersionCreate(
        version_number=1,
        file_path="/test/path/document.pdf",
        file_size=1024,
        checksum="abc123",
        document_id=test_document.id,
        created_by_id=test_user.id
    )
    db_version = create_document_version(db_session, version_data)
    assert db_version.version_number == 1
    assert db_version.file_path == "/test/path/document.pdf"
    assert db_version.file_size == 1024
    assert db_version.checksum == "abc123"
    assert db_version.document_id == test_document.id
    assert db_version.created_by_id == test_user.id

def test_get_document_version(db_session, test_user, test_document):
    version_data = DocumentVersionCreate(
        version_number=1,
        file_path="/test/path/document.pdf",
        file_size=1024,
        checksum="abc123",
        document_id=test_document.id,
        created_by_id=test_user.id
    )
    created_version = create_document_version(db_session, version_data)
    retrieved_version = get_document_version(db_session, created_version.id)
    assert retrieved_version.id == created_version.id
    assert retrieved_version.version_number == 1
    assert retrieved_version.file_path == "/test/path/document.pdf"
    assert retrieved_version.file_size == 1024
    assert retrieved_version.checksum == "abc123"

def test_get_document_versions(db_session, test_user, test_document):
    versions = []
    for i in range(3):
        version_data = DocumentVersionCreate(
            version_number=i + 1,
            file_path=f"/test/path/document_v{i+1}.pdf",
            file_size=1024 * (i + 1),
            checksum=f"abc{i+1}23",
            document_id=test_document.id,
            created_by_id=test_user.id
        )
        version = create_document_version(db_session, version_data)
        versions.append(version)
    
    retrieved_versions = get_document_versions(db_session, test_document.id)
    assert len(retrieved_versions) == 3
    for i, version in enumerate(retrieved_versions):
        assert version.version_number == i + 1
        assert version.file_path == f"/test/path/document_v{i+1}.pdf"
        assert version.file_size == 1024 * (i + 1)
        assert version.checksum == f"abc{i+1}23"

def test_update_document_version(db_session, test_user, test_document):
    version_data = DocumentVersionCreate(
        version_number=1,
        file_path="/test/path/original.pdf",
        file_size=1024,
        checksum="abc123",
        document_id=test_document.id,
        created_by_id=test_user.id
    )
    created_version = create_document_version(db_session, version_data)
    
    update_data = DocumentVersionUpdate(
        file_path="/test/path/updated.pdf",
        file_size=2048,
        checksum="def456"
    )
    updated_version = update_document_version(db_session, created_version.id, update_data)
    assert updated_version.file_path == "/test/path/updated.pdf"
    assert updated_version.file_size == 2048
    assert updated_version.checksum == "def456"

def test_delete_document_version(db_session, test_user, test_document):
    version_data = DocumentVersionCreate(
        version_number=1,
        file_path="/test/path/document.pdf",
        file_size=1024,
        checksum="abc123",
        document_id=test_document.id,
        created_by_id=test_user.id
    )
    created_version = create_document_version(db_session, version_data)
    delete_document_version(db_session, created_version.id)
    deleted_version = get_document_version(db_session, created_version.id)
    assert deleted_version is None

def test_get_document_version_by_version_number(db_session, test_user, test_document):
    version_data = DocumentVersionCreate(
        version_number=1,
        file_path="/test/path/document.pdf",
        file_size=1024,
        checksum="abc123",
        document_id=test_document.id,
        created_by_id=test_user.id
    )
    created_version = create_document_version(db_session, version_data)
    retrieved_version = get_document_version_by_version_number(db_session, test_document.id, 1)
    assert retrieved_version.id == created_version.id
    assert retrieved_version.version_number == 1
    assert retrieved_version.file_path == "/test/path/document.pdf"
    assert retrieved_version.file_size == 1024
    assert retrieved_version.checksum == "abc123" 