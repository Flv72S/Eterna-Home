from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User
    from app.models.bim_model import BIMModel

class DocumentVersion(SQLModel, table=True):
    """Modello per il versionamento dei documenti."""
    __tablename__ = "document_versions"
    __table_args__ = {'extend_existing': True}

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    version_number: int = Field(index=True)
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Foreign keys
    document_id: Optional[int] = Field(default=None, foreign_key="documents.id", index=True)
    bim_model_id: Optional[int] = Field(default=None, foreign_key="bim_models.id", index=True)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    
    # Relationships
    document: Optional["Document"] = Relationship(back_populates="versions")
    bim_model: Optional["BIMModel"] = Relationship(back_populates="versions")
    # created_by: Optional["User"] = Relationship(back_populates="document_versions") 