from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.node import Node
    from app.models.document import Document
    from app.models.room import Room

class House(SQLModel, table=True):
    """Modello per la gestione delle case."""
    
    __tablename__ = "houses"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    address: str
    owner_id: int = Field(foreign_key="user.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    owner: "User" = Relationship(back_populates="houses", sa_relationship_kwargs={"lazy": "select"})
    nodes: List["Node"] = Relationship(back_populates="house")
    documents: List["Document"] = Relationship(
        back_populates="house",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    rooms: List["Room"] = Relationship(back_populates="house") 