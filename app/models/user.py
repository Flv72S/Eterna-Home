from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from pydantic import ConfigDict, EmailStr
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from app.models.user_role import UserRole

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.booking import Booking
    from app.models.role import Role
else:
    from app.models.role import UserRole

class User(SQLModel, table=True):
    """
    Modello User per l'autenticazione e l'autorizzazione.
    Utilizza SQLModel per combinare le funzionalità di Pydantic e SQLAlchemy.
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,
        extra='allow',
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

    # Campi primari e indici
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Campi di stato
    is_verified: bool = Field(default=False, description="Indica se l'email dell'utente è verificata")

    # Campi di audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    houses: List["House"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    documents: List["Document"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    document_versions: List["DocumentVersion"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "DocumentVersion.created_by_id", "cascade": "all, delete-orphan"}
    )
    bookings: List["Booking"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    # Relazione many-to-many con Role
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
        sa_relationship_kwargs={
            "primaryjoin": "User.id == UserRole.user_id",
            "secondaryjoin": "UserRole.role_id == Role.id"
        }
    )

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
        
    def has_role(self, role_name: str) -> bool:
        """Verifica se l'utente ha un ruolo specifico."""
        return any(role.name == role_name and role.is_active for role in self.roles)
        
    def has_any_role(self, role_names: List[str]) -> bool:
        """Verifica se l'utente ha almeno uno dei ruoli specificati."""
        return any(self.has_role(role_name) for role_name in role_names)
        
    def get_role_names(self) -> List[str]:
        """Restituisce la lista dei nomi dei ruoli attivi dell'utente."""
        return [role.name for role in self.roles if role.is_active] 