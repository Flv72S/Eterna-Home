from datetime import datetime, UTC
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID

class DocumentVersion(SQLModel, table=True):
    __tablename__ = "document_versions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    document_id: int = Field(foreign_key="documents.id", nullable=False)
    version_number: int = Field(nullable=False)
    user_id: UUID = Field(nullable=False)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    storage_path: str = Field(nullable=False)
    change_description: Optional[str] = None
    previous_version_id: Optional[int] = Field(default=None, foreign_key="document_versions.id")

    # Relazioni
    document: "Document" = Relationship(back_populates="versions")
    previous_version: Optional["DocumentVersion"] = Relationship(
        back_populates="next_version",
        sa_relationship_kwargs={"remote_side": "DocumentVersion.id"}
    )
    next_version: Optional["DocumentVersion"] = Relationship(
        back_populates="previous_version",
        sa_relationship_kwargs={"remote_side": "DocumentVersion.previous_version_id"}
    )

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field(nullable=False)
    content: Optional[str] = None
    node_id: int = Field(foreign_key="nodes.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)})
    
    # Relazione con le versioni
    versions: List[DocumentVersion] = Relationship(back_populates="document") 