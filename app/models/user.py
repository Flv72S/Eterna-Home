from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, DateTime, String, Boolean, Integer, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document

class User(SQLModel, table=True):
    """
    Modello User per l'autenticazione e l'autorizzazione.
    Utilizza SQLModel per combinare le funzionalità di Pydantic e SQLAlchemy.
    """
    __tablename__ = "users"
    
    # Configurazione Pydantic
    model_config = ConfigDict(
        from_attributes=True,  # equivalente a orm_mode=True
        populate_by_name=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )

    # Campi primari e indici
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        index=True,
        unique=True,
        min_length=3,
        max_length=50,
        description="Username univoco dell'utente"
    )
    email: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Email univoca dell'utente"
    )
    hashed_password: str = Field(
        min_length=60,
        max_length=60,
        description="Password hashata dell'utente"
    )

    # Campi di stato
    is_active: bool = Field(default=True, description="Indica se l'utente è attivo")
    is_superuser: bool = Field(default=False, description="Indica se l'utente è un superuser")
    is_verified: bool = Field(default=False, description="Indica se l'email dell'utente è verificata")

    # Campi di audit
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Data e ora di creazione dell'utente"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc)),
        description="Data e ora dell'ultimo aggiornamento dell'utente"
    )
    last_login: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Data e ora dell'ultimo accesso dell'utente"
    )

    # Campi aggiuntivi
    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nome completo dell'utente"
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Numero di telefono dell'utente"
    )

    # Relazioni
    houses: List["House"] = Relationship(back_populates="owner", sa_relationship_kwargs={"lazy": "select"})
    documents: List["Document"] = Relationship(back_populates="author")

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def is_authenticated(self) -> bool:
        """Indica se l'utente è autenticato."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Indica se l'utente è anonimo."""
        return False 