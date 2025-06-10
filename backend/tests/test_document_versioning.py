import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4
from app.models.document import Document, DocumentVersion
from app.models.node import Node
from sqlalchemy.orm import Session
from sqlalchemy import text

def test_migration_creates_versioning_table(db: Session):
    """Verifica che la migrazione abbia creato correttamente la tabella document_versions."""
    # Verifica che la tabella esista
    result = db.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'document_versions'
        );
    """)).scalar()
    assert result is True

    # Verifica la struttura della tabella
    columns = db.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'document_versions'
        ORDER BY ordinal_position;
    """)).fetchall()
    
    expected_columns = {
        'id': ('integer', 'NO'),
        'document_id': ('integer', 'NO'),
        'version_number': ('integer', 'NO'),
        'user_id': ('uuid', 'NO'),
        'timestamp': ('timestamp with time zone', 'NO'),
        'storage_path': ('character varying', 'NO'),
        'change_description': ('character varying', 'YES'),
        'previous_version_id': ('integer', 'YES')
    }
    
    for column in columns:
        name, type_, nullable = column
        assert name in expected_columns
        assert type_ == expected_columns[name][0]
        assert nullable == expected_columns[name][1]

def test_create_versioning_record(db: Session):
    """Test per la creazione di record di versioning e verifica delle relazioni."""
    # Crea un nodo di test
    node = Node(
        name="Test Node",
        type="Test Type",
        location="Test Location",
        status="active"
    )
    db.add(node)
    db.commit()
    
    # Crea un documento di test
    document = Document(
        title="Test Document",
        content="Initial content",
        node_id=node.id
    )
    db.add(document)
    db.commit()
    
    # Crea la prima versione
    user_id = uuid4()
    version1 = DocumentVersion(
        document_id=document.id,
        version_number=1,
        user_id=user_id,
        storage_path="/path/to/version1",
        change_description="Initial version"
    )
    db.add(version1)
    db.commit()
    
    # Verifica la prima versione
    assert version1.id is not None
    assert version1.version_number == 1
    assert version1.previous_version_id is None
    assert version1.document == document
    assert version1 in document.versions
    
    # Crea la seconda versione
    version2 = DocumentVersion(
        document_id=document.id,
        version_number=2,
        user_id=user_id,
        storage_path="/path/to/version2",
        change_description="Updated content",
        previous_version_id=version1.id
    )
    db.add(version2)
    db.commit()
    
    # Verifica la seconda versione
    assert version2.id is not None
    assert version2.version_number == 2
    assert version2.previous_version_id == version1.id
    assert version2.previous_version == version1
    assert version1.next_version == version2
    
    # Verifica la coerenza delle versioni
    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document.id
    ).order_by(DocumentVersion.version_number).all()
    
    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[1].version_number == 2
    assert versions[1].previous_version_id == versions[0].id 

    # maintenance_record = create_random_maintenance_record(db, node=node, user=user) 