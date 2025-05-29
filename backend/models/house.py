from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.node import Node
    from backend.models.legacy_documents import LegacyDocument
    from backend.models.bim import BIM
    from backend.models.maintenance import Maintenance

class House(SQLModel, table=True):
    __tablename__ = "houses"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    address: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    owner_id: int = Field(foreign_key="users.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    owner: Optional["User"] = Relationship(back_populates="houses")
    nodes: List["Node"] = Relationship(back_populates="house", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    legacy_documents: List["LegacyDocument"] = Relationship(back_populates="house", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    bim_files: List["BIM"] = Relationship(back_populates="house", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    maintenance_tasks: List["Maintenance"] = Relationship(back_populates="house") 