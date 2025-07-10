from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .document_version import DocumentVersion
    from .bim_fragment import BIMFragment

class BIMModel(SQLModel, table=True):
    __tablename__ = "bim_models"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    file_path: str = Field(max_length=500)
    file_size: int
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="pending", max_length=50)
    conversion_progress: int = Field(default=0)
    house_id: Optional[int] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None, max_length=255)
    
    # Relazioni
    versions: List["DocumentVersion"] = Relationship(back_populates="bim_model")
    fragments: List["BIMFragment"] = Relationship(back_populates="bim_model")
    
    model_config = {"arbitrary_types_allowed": True} 