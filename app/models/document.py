from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.house import House
    from app.models.node import Node

class Document(SQLModel, table=True):
    """Modello per la rappresentazione di un documento nel database."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "manuale_installazione.pdf",
                "type": "application/pdf",
                "size": 1024576,
                "path": "/documents/manuali/manuale_installazione.pdf",
                "checksum": "a1b2c3d4e5f6...",
                "house_id": 1
            }
        }
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Nome del documento")
    type: str = Field(description="MIME type del documento")
    size: int = Field(description="Dimensione del documento in bytes")
    upload_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data e ora di upload"
    )
    author_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        description="ID dell'utente che ha caricato il documento"
    )
    path: str = Field(description="Percorso del file su storage")
    checksum: str = Field(description="Hash SHA256 del contenuto file")
    house_id: Optional[int] = Field(
        default=None,
        foreign_key="house.id",
        description="ID della casa associata al documento"
    )
    node_id: Optional[int] = Field(
        default=None,
        foreign_key="node.id",
        description="ID del nodo associato al documento"
    )

    # Relazioni
    author: Optional["User"] = Relationship(back_populates="documents")
    house: Optional["House"] = Relationship(back_populates="documents")
    node: Optional["Node"] = Relationship(back_populates="documents") 