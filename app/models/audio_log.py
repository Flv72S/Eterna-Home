from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid
from sqlmodel import Field, select, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.node import Node
    from app.models.house import House

class AudioLogCreate(SQLModel):
    """Modello per la creazione di un AudioLog."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    user_id: int = Field(description="ID dell'utente che ha inviato il comando")
    node_id: Optional[int] = Field(default=None, description="ID del nodo associato")
    house_id: Optional[int] = Field(default=None, description="ID della casa associata")
    transcribed_text: Optional[str] = Field(default=None, max_length=1000, description="Testo trascritto dal comando vocale")
    response_text: Optional[str] = Field(default=None, max_length=1000, description="Risposta generata dal sistema")
    processing_status: str = Field(default="received", description="Stato di elaborazione del comando")

class AudioLogUpdate(SQLModel):
    """Modello per l'aggiornamento di un AudioLog."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    transcribed_text: Optional[str] = Field(default=None, max_length=1000)
    response_text: Optional[str] = Field(default=None, max_length=1000)
    processing_status: Optional[str] = None
    audio_url: Optional[str] = Field(default=None, max_length=500)

class AudioLog(SQLModel, table=True):
    """Modello per la rappresentazione di un AudioLog nel database."""
    __tablename__ = "audio_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    house_id: int = Field(foreign_key="houses.id")
    file_url: str
    file_size: int
    duration: float
    transcript: Optional[str] = None
    status: str = Field(default="pending")
    tenant_id: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Campo tenant_id per multi-tenancy
    # tenant_id: uuid.UUID = Field(
    #     default_factory=uuid.uuid4,
    #     index=True,
    #     description="ID del tenant per isolamento logico multi-tenant"
    # )
    
    # Relazioni
    # user: Optional["User"] = Relationship(back_populates="audio_logs")
    # node: Optional["Node"] = Relationship(back_populates="audio_logs")
    # house: Optional["House"] = Relationship(back_populates="audio_logs")

    @property
    def status_display(self) -> str:
        """Restituisce il nome di visualizzazione dello stato."""
        status_map = {
            "received": "Ricevuto",
            "transcribing": "In Trascrizione",
            "analyzing": "In Analisi",
            "completed": "Completato",
            "failed": "Fallito"
        }
        return status_map.get(self.processing_status, self.processing_status)

    @property
    def is_completed(self) -> bool:
        """Verifica se l'elaborazione è completata."""
        return self.processing_status in ["completed", "failed"]

    @property
    def is_processing(self) -> bool:
        """Verifica se l'elaborazione è in corso."""
        return self.processing_status in ["transcribing", "analyzing"]

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 