from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.document import Document

class Versioning(SQLModel, table=True):
    __tablename__ = "versioning"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", nullable=False)
    version_number: str = Field(max_length=50, nullable=False)
    file_path: str = Field(max_length=255, nullable=False)
    changes_description: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    document: "Document" = Relationship(back_populates="versions") 