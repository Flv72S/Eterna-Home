from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
import uuid
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
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    document_type: Optional[str] = Field(default="general", description="Tipo di documento (general, contract, manual, etc.)")
    file_url: str = Field(description="URL del file in storage")
    file_size: int = Field(description="Dimensione del file in bytes")
    file_type: str = Field(description="Tipo MIME del file")
    checksum: str = Field(description="Checksum SHA-256 del file")
    
    # Campo tenant_id per multi-tenancy
    tenant_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        index=True,
        description="ID del tenant"
    )
    
    # Campo per tracciare il proprietario del documento
    owner_id: int = Field(foreign_key="users.id", description="ID del proprietario del documento")
    
    # Campo per tracciare file cifrati
    is_encrypted: bool = Field(default=False, description="Indica se il file è cifrato")
    
    # Campi specifici per manuali PDF
    device_name: Optional[str] = Field(default=None, description="Nome dell'oggetto/elettrodomestico")
    brand: Optional[str] = Field(default=None, description="Marca dell'oggetto")
    model: Optional[str] = Field(default=None, description="Modello dell'oggetto")
    external_link: Optional[str] = Field(default=None, description="Link esterno al manuale (se non caricato)")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id", description="ID della stanza associata")
    
    # Relazioni
    # owner: "User" = Relationship(back_populates="documents")
    house_id: Optional[int] = Field(default=None, foreign_key="houses.id")
    node_id: Optional[int] = Field(default=None, foreign_key="nodes.id")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    # node: Optional["Node"] = Relationship(back_populates="documents")
    versions: List["DocumentVersion"] = Relationship(
        back_populates="document"
    )

    # Metodi multi-tenant (simulazione del mixin)
    @classmethod
    def filter_by_tenant(cls, session, tenant_id: str, **filters):
        """Filtra i documenti per tenant_id e altri filtri opzionali."""
        from sqlmodel import select
        query = select(cls).where(cls.tenant_id == tenant_id)
        
        # Applica filtri aggiuntivi
        for field, value in filters.items():
            if hasattr(cls, field) and value is not None:
                query = query.where(getattr(cls, field) == value)
        
        result = session.exec(query)
        return list(result.all())
    
    @classmethod
    def get_by_id_and_tenant(cls, session, item_id: int, tenant_id: str):
        """Ottiene un documento specifico verificando che appartenga al tenant."""
        from sqlmodel import select
        query = select(cls).where(
            cls.id == item_id,
            cls.tenant_id == tenant_id
        )
        result = session.exec(query)
        return result.first()
    
    @classmethod
    def update_with_tenant_check(cls, session, item_id: int, tenant_id: str, **update_data):
        """Aggiorna un documento verificando che appartenga al tenant."""
        item = cls.get_by_id_and_tenant(session, item_id, tenant_id)
        if not item:
            return None
        
        # Aggiorna i campi
        for field, value in update_data.items():
            if hasattr(item, field):
                setattr(item, field, value)
        
        session.commit()
        session.refresh(item)
        return item
    
    @classmethod
    def delete_with_tenant_check(cls, session, item_id: int, tenant_id: str):
        """Elimina un documento verificando che appartenga al tenant."""
        item = cls.get_by_id_and_tenant(session, item_id, tenant_id)
        if not item:
            return False
        
        session.delete(item)
        session.commit()
        return True

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 