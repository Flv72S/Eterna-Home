from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User

class UserTenantRole(SQLModel, table=True):
    """
    Modello pivot per gestire le associazioni utente-tenant-ruolo.
    Permette a un utente di avere ruoli diversi in tenant diversi.
    
    Esempi di utilizzo:
    - Progettista esterno che lavora su più progetti (tenant)
    - Tecnico multi-condominio con ruoli diversi
    - Amministratore delegato di gruppo con accesso a più aziende
    """
    __tablename__ = "user_tenant_roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Chiavi esterne
    user_id: int = Field(foreign_key="users.id", index=True, description="ID dell'utente")
    tenant_id: str = Field(index=True, description="ID del tenant")
    
    # Ruolo dell'utente nel tenant specifico
    role: str = Field(..., description="Ruolo dell'utente all'interno del tenant")
    
    # Stato dell'associazione
    is_active: bool = Field(default=True, description="Indica se l'associazione è attiva")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    # user: Optional["User"] = Relationship(back_populates="tenant_roles")
    
    # Metodi helper
    def __repr__(self) -> str:
        return f"<UserTenantRole user_id={self.user_id} tenant_id={self.tenant_id} role={self.role}>"
    
    @property
    def is_valid(self) -> bool:
        """Verifica se l'associazione è valida e attiva."""
        return self.is_active
    
    # Metodi di classe per query comuni
    @classmethod
    def get_user_roles_in_tenant(cls, session, user_id: int, tenant_id: str):
        """Ottiene tutti i ruoli di un utente in un tenant specifico."""
        from sqlmodel import select
        query = select(cls).where(
            cls.user_id == user_id,
            cls.tenant_id == tenant_id,
            cls.is_active == True
        )
        result = session.exec(query)
        return list(result.all())
    
    @classmethod
    def get_user_tenants(cls, session, user_id: int):
        """Ottiene tutti i tenant a cui un utente è associato."""
        from sqlmodel import select
        query = select(cls.tenant_id).where(
            cls.user_id == user_id,
            cls.is_active == True
        ).distinct()
        result = session.exec(query)
        return [row.tenant_id for row in result.all()]
    
    @classmethod
    def get_tenant_users(cls, session, tenant_id: str):
        """Ottiene tutti gli utenti associati a un tenant."""
        from sqlmodel import select
        query = select(cls).where(
            cls.tenant_id == tenant_id,
            cls.is_active == True
        )
        result = session.exec(query)
        return list(result.all())
    
    @classmethod
    def has_role_in_tenant(cls, session, user_id: int, tenant_id: str, role: str) -> bool:
        """Verifica se un utente ha un ruolo specifico in un tenant."""
        from sqlmodel import select
        query = select(cls).where(
            cls.user_id == user_id,
            cls.tenant_id == tenant_id,
            cls.role == role,
            cls.is_active == True
        )
        result = session.exec(query)
        return result.first() is not None
    
    @classmethod
    def has_any_role_in_tenant(cls, session, user_id: int, tenant_id: str, roles: list) -> bool:
        """Verifica se un utente ha almeno uno dei ruoli specificati in un tenant."""
        from sqlmodel import select
        query = select(cls).where(
            cls.user_id == user_id,
            cls.tenant_id == tenant_id,
            cls.role.in_(roles),
            cls.is_active == True
        )
        result = session.exec(query)
        return result.first() is not None
    
    @classmethod
    def add_user_to_tenant(cls, session, user_id: int, tenant_id: str, role: str):
        """Aggiunge un utente a un tenant con un ruolo specifico."""
        from sqlmodel import select
        # Verifica se l'associazione esiste già
        existing = session.exec(
            select(cls).where(
                cls.user_id == user_id,
                cls.tenant_id == tenant_id
            )
        ).first()
        
        if existing:
            # Aggiorna il ruolo esistente
            existing.role = role
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            session.add(existing)
        else:
            # Crea una nuova associazione
            new_association = cls(
                user_id=user_id,
                tenant_id=tenant_id,
                role=role
            )
            session.add(new_association)
        
        session.commit()
        return existing or new_association
    
    @classmethod
    def remove_user_from_tenant(cls, session, user_id: int, tenant_id: str):
        """Rimuove un utente da un tenant (disattiva l'associazione)."""
        from sqlmodel import select
        association = session.exec(
            select(cls).where(
                cls.user_id == user_id,
                cls.tenant_id == tenant_id
            )
        ).first()
        
        if association:
            association.is_active = False
            association.updated_at = datetime.now(timezone.utc)
            session.add(association)
            session.commit()
            return True
        
        return False

    # TODO: Aggiungere migrazione Alembic per la tabella user_tenant_roles
    # TODO: Implementare logica per assegnazione automatica durante la registrazione
    # TODO: Aggiungere validazione ruoli per tenant specifici 