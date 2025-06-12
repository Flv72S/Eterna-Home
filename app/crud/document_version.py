from typing import List, Optional
from sqlmodel import Session, select
from app.models.document_version import DocumentVersion
from app.schemas.document_version import DocumentVersionCreate, DocumentVersionUpdate

def create_document_version(
    db: Session,
    version: DocumentVersionCreate
) -> DocumentVersion:
    db_version = DocumentVersion(
        version_number=version.version_number,
        file_path=version.file_path,
        file_size=version.file_size,
        checksum=version.checksum,
        document_id=version.document_id,
        created_by_id=version.created_by_id
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def get_document_version(
    db: Session,
    version_id: int
) -> Optional[DocumentVersion]:
    result = db.execute(
        select(DocumentVersion).where(DocumentVersion.id == version_id)
    )
    return result.scalar_one_or_none()

def get_document_versions(
    db: Session,
    document_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[DocumentVersion]:
    result = db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

def update_document_version(
    db: Session,
    version_id: int,
    version: DocumentVersionUpdate
) -> Optional[DocumentVersion]:
    db_version = get_document_version(db, version_id)
    if db_version is None:
        return None
    
    update_data = version.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_version, field, value)
    
    db.commit()
    db.refresh(db_version)
    return db_version

def delete_document_version(
    db: Session,
    version_id: int
) -> bool:
    db_version = get_document_version(db, version_id)
    if db_version is None:
        return False
    
    db.delete(db_version)
    db.commit()
    return True

def get_document_version_by_version_number(
    db: Session,
    document_id: int,
    version_number: int
) -> Optional[DocumentVersion]:
    result = db.execute(
        select(DocumentVersion)
        .where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        )
    )
    return result.scalar_one_or_none() 