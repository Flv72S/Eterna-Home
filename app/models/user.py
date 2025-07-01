from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING, Any
import uuid

from pydantic import ConfigDict, EmailStr
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from app.models.enums import UserRole as UserRoleEnum
from app.models.permission import UserPermission
from typing_extensions import Annotated
from sqlalchemy.orm import Mapped

if TYPE_CHECKING:
    from app.models.house import House
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.booking import Booking
    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.models.user_tenant_role import UserTenantRole
    from app.models.user_house import UserHouse
    from app.models.bim_model import BIMModel
    from app.models.bim_model import BIMModelVersion
    from app.models.audio_log import AudioLog
    from app.models.permission import Permission
else:
    from app.models.role import Role
    from app.models.user_role import UserRole
    from app.models.user_tenant_role import UserTenantRole
    from app.models.user_house import UserHouse

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
        },
        protected_namespaces=()
    )

    # Campi primari e indici
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Campo tenant_id per multi-tenancy (tenant principale)
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant principale per isolamento logico multi-tenant"
    )

    # Campo ruolo principale
    role: str = Field(
        default=UserRoleEnum.get_default_role(),
        description="Ruolo principale dell'utente"
    )

    # Campi di stato
    is_verified: bool = Field(default=False, description="Indica se l'email dell'utente è verificata")
    
    # Campi MFA (Multi-Factor Authentication)
    mfa_enabled: bool = Field(default=False, description="Indica se l'MFA è abilitato per l'utente")
    mfa_secret: Optional[str] = Field(default=None, description="Segreto TOTP per l'MFA")

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

    # Relazioni (temporaneamente commentate per compatibilità SQLAlchemy 2.0+)
    # roles: Any = Relationship(
    #     back_populates="users",
    #     link_model=UserRole
    # )
    # tenant_roles: Any = Relationship(
    #     back_populates="user",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    # )
    # permissions: Any = Relationship(
    #     back_populates="users",
    #     link_model=UserPermission
    # )

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
        # Controlla il ruolo principale
        if self.role == role_name:
            return True
        
        # Controlla i ruoli assegnati tramite la relazione many-to-many
        if hasattr(self, 'roles') and self.roles:
            return any(role.name == role_name and role.is_active for role in self.roles)
        
        return False
        
    def has_any_role(self, role_names: List[str]) -> bool:
        """Verifica se l'utente ha almeno uno dei ruoli specificati."""
        # Controlla il ruolo principale
        if self.role in role_names:
            return True
        
        # Controlla i ruoli assegnati tramite la relazione many-to-many
        if hasattr(self, 'roles') and self.roles:
            return any(role.name in role_names and role.is_active for role in self.roles)
        
        return False
        
    def get_role_names(self) -> List[str]:
        """Restituisce la lista dei nomi dei ruoli attivi dell'utente."""
        role_names = []
        
        # Aggiungi il ruolo principale se presente
        if self.role:
            role_names.append(self.role)
        
        # Aggiungi i ruoli assegnati tramite la relazione many-to-many
        if hasattr(self, 'roles') and self.roles:
            for role in self.roles:
                if role.is_active and role.name not in role_names:
                    role_names.append(role.name)
        
        return role_names
    
    def has_role_in_tenant(self, role_name: str, tenant_id: uuid.UUID) -> bool:
        """Verifica se l'utente ha un ruolo specifico in un tenant."""
        # Usa il metodo di classe di UserTenantRole per evitare problemi di relazioni
        from app.models.user_tenant_role import UserTenantRole
        from app.db.session import get_session
        
        with next(get_session()) as session:
            return UserTenantRole.has_role_in_tenant(session, self.id, tenant_id, role_name)
    
    def has_any_role_in_tenant(self, role_names: List[str], tenant_id: uuid.UUID) -> bool:
        """Verifica se l'utente ha almeno uno dei ruoli specificati in un tenant."""
        # Usa il metodo di classe di UserTenantRole per evitare problemi di relazioni
        from app.models.user_tenant_role import UserTenantRole
        from app.db.session import get_session
        
        with next(get_session()) as session:
            return UserTenantRole.has_any_role_in_tenant(session, self.id, tenant_id, role_names)
    
    def get_roles_in_tenant(self, tenant_id: uuid.UUID) -> List[str]:
        """Restituisce la lista dei ruoli dell'utente in un tenant specifico."""
        # Usa il metodo di classe di UserTenantRole per evitare problemi di relazioni
        from app.models.user_tenant_role import UserTenantRole
        from app.db.session import get_session
        
        with next(get_session()) as session:
            roles = UserTenantRole.get_user_roles_in_tenant(session, self.id, tenant_id)
            return [role.role for role in roles]
    
    def get_tenant_ids(self) -> List[uuid.UUID]:
        """Restituisce la lista degli ID dei tenant a cui l'utente appartiene."""
        # Usa il metodo di classe di UserTenantRole per evitare problemi di relazioni
        from app.models.user_tenant_role import UserTenantRole
        from app.db.session import get_session
        
        with next(get_session()) as session:
            tenant_ids = UserTenantRole.get_user_tenants(session, self.id)
            # Aggiungi il tenant principale se non è già presente
            if self.tenant_id not in tenant_ids:
                tenant_ids.append(self.tenant_id)
            return list(set(tenant_ids))
    
    def get_house_ids(self, tenant_id: Optional[uuid.UUID] = None) -> List[int]:
        """
        Restituisce la lista degli ID delle case a cui l'utente ha accesso.
        Se tenant_id è specificato, filtra solo per quel tenant.
        """
        house_ids = []
        
        # Case di cui è proprietario
        if hasattr(self, 'owned_houses') and self.owned_houses:
            for house in self.owned_houses:
                if tenant_id is None or house.tenant_id == tenant_id:
                    house_ids.append(house.id)
        
        # Case associate tramite UserHouse
        if hasattr(self, 'user_houses') and self.user_houses:
            for user_house in self.user_houses:
                if user_house.is_active and (tenant_id is None or user_house.tenant_id == tenant_id):
                    house_ids.append(user_house.house_id)
        
        return list(set(house_ids))
    
    def has_house_access(self, house_id: int, tenant_id: Optional[uuid.UUID] = None) -> bool:
        """
        Verifica se l'utente ha accesso a una casa specifica.
        Se tenant_id è specificato, verifica anche l'appartenenza al tenant.
        """
        # Verifica se è proprietario della casa
        if hasattr(self, 'owned_houses') and self.owned_houses:
            for house in self.owned_houses:
                if house.id == house_id:
                    if tenant_id is None or house.tenant_id == tenant_id:
                        return True
        
        # Verifica se è associato tramite UserHouse
        if hasattr(self, 'user_houses') and self.user_houses:
            for user_house in self.user_houses:
                if (user_house.house_id == house_id and 
                    user_house.is_active and 
                    (tenant_id is None or user_house.tenant_id == tenant_id)):
                    return True
        
        return False
    
    def get_role_in_house(self, house_id: int, tenant_id: Optional[uuid.UUID] = None) -> Optional[str]:
        """
        Restituisce il ruolo dell'utente in una casa specifica.
        Se tenant_id è specificato, verifica anche l'appartenenza al tenant.
        """
        # Verifica se è proprietario della casa
        if hasattr(self, 'owned_houses') and self.owned_houses:
            for house in self.owned_houses:
                if house.id == house_id:
                    if tenant_id is None or house.tenant_id == tenant_id:
                        return "owner"
        
        # Verifica ruolo tramite UserHouse
        if hasattr(self, 'user_houses') and self.user_houses:
            for user_house in self.user_houses:
                if (user_house.house_id == house_id and 
                    user_house.is_active and 
                    (tenant_id is None or user_house.tenant_id == tenant_id)):
                    return user_house.role_in_house
        
        return None
    
    def can_access_admin_features(self) -> bool:
        """Verifica se l'utente può accedere alle funzionalità amministrative."""
        admin_roles = UserRoleEnum.get_admin_roles()
        return self.role in admin_roles
    
    def can_manage_users(self) -> bool:
        """Verifica se l'utente può gestire gli utenti."""
        return self.role in ["super_admin", "admin"]
    
    def can_manage_roles(self) -> bool:
        """Verifica se l'utente può gestire i ruoli."""
        return self.role == "super_admin"
    
    def get_display_role(self) -> str:
        """Restituisce il nome visualizzabile del ruolo."""
        return UserRoleEnum.get_display_name(self.role)
    
    @property
    def role_display(self) -> str:
        """Proprietà per il nome visualizzato del ruolo (usata dagli schemi Pydantic)."""
        return UserRoleEnum.get_display_name(self.role)

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 