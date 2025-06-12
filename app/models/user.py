from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Column, DateTime, String, Boolean, Integer, Relationship
from pydantic import ConfigDict, EmailStr
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.booking import Booking

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False

class User(UserBase, table=True):
    """
    Modello User per l'autenticazione e l'autorizzazione.
    Utilizza SQLModel per combinare le funzionalità di Pydantic e SQLAlchemy.
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )

    # Campi primari e indici
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Campi di stato
    is_verified: bool = Field(default=False, description="Indica se l'email dell'utente è verificata")

    # Campi di audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
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
    houses: List["House"] = Relationship(back_populates="owner")
    documents: List["Document"] = Relationship(back_populates="owner")
    document_versions: List["DocumentVersion"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "DocumentVersion.created_by_id"}
    )
    bookings: List["Booking"] = Relationship(back_populates="user")

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

class UserCreate(UserBase):
    password: str

class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserRead(UserBase):
    id: int 