from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .bim_model import BIMModel
    from .document import Document

class DocumentVersion(SQLModel, table=True):
    __tablename__ = "document_versions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    version_number: int
    file_path: str = Field(max_length=500)
    file_size: int
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = Field(default=None, max_length=1000)
    bim_model_id: Optional[int] = Field(default=None, foreign_key="bim_models.id")
    document_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    
    # Relazioni
    bim_model: Optional["BIMModel"] = Relationship(back_populates="versions")
    document: Optional["Document"] = Relationship(back_populates="versions")
    
    model_config = {"arbitrary_types_allowed": True} 