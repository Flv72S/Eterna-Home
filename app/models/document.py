from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.house import House
    from app.models.node import Node
    from app.models.document_version import DocumentVersion

class Document(SQLModel, table=True):
    """Modello per la gestione dei documenti."""
    __tablename__ = "documents"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    file_url: str = Field(description="URL del file in storage")
    file_size: int = Field(description="Dimensione del file in bytes")
    file_type: str = Field(description="Tipo MIME del file")
    checksum: str = Field(description="Checksum SHA-256 del file")
    
    # Relazioni
    owner_id: int = Field(foreign_key="users.id")
    house_id: Optional[int] = Field(default=None, foreign_key="houses.id")
    node_id: Optional[int] = Field(default=None, foreign_key="nodes.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    owner: "User" = Relationship(back_populates="documents")
    house: Optional["House"] = Relationship(back_populates="documents")
    node: Optional["Node"] = Relationship(back_populates="documents")
    versions: List["DocumentVersion"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    ) 