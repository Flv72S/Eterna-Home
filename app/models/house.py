from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.node import Node, NodeArea, MainArea
    from app.models.document import Document
    from app.models.room import Room
    from app.models.bim_model import BIMModel
    from app.models.audio_log import AudioLog
    from app.models.user_house import UserHouse

class House(SQLModel, table=True):
    """Modello per la gestione delle case."""
    
    __tablename__ = "houses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    address: str
    owner_id: int = Field(foreign_key="users.id")
    
    # Campo tenant_id per multi-tenancy
    tenant_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    # Proprietario della casa (relazione one-to-many) - temporaneamente commentata
    # owner: "User" = Relationship(back_populates="owned_houses", sa_relationship_kwargs={"lazy": "select"})
    
    # Utenti associati alla casa (relazione many-to-many tramite UserHouse) - temporaneamente commentata
    # users: List["User"] = Relationship(
    #     back_populates="houses",
    #     link_model="UserHouse",
    #     sa_relationship_kwargs={
    #         "primaryjoin": "House.id == UserHouse.house_id",
    #         "secondaryjoin": "UserHouse.user_id == User.id"
    #     }
    # )
    
    # Relazione con UserHouse per accesso diretto alle associazioni - temporaneamente commentata
    # user_houses: List["UserHouse"] = Relationship(
    #     back_populates="house",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    # )
    
    # Documenti associati alla casa - temporaneamente commentata
    # documents: List["Document"] = Relationship(back_populates="house")
    
    # Relazioni con Node - temporaneamente commentate
    # nodes: List["Node"] = Relationship(back_populates="house")
    # node_areas: List["NodeArea"] = Relationship(back_populates="house")
    # main_areas: List["MainArea"] = Relationship(back_populates="house")
    
    # Relazioni con BIMModel e AudioLog - temporaneamente commentate
    # bim_models: List["BIMModel"] = Relationship(
    #     back_populates="house",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    # )
    # audio_logs: List["AudioLog"] = Relationship(back_populates="house")

    # TODO: Aggiungere migrazione Alembic per il campo tenant_id
    # TODO: Implementare logica per assegnazione automatica tenant_id durante la creazione
    # TODO: Aggiungere filtri multi-tenant nelle query CRUD 