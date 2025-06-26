"""
Modello per la gestione degli attivatori fisici con supporto multi-tenant.
Gestisce NFC, BLE, QR Code e altri attivatori fisici collegati ai nodi.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from pydantic import ConfigDict

if TYPE_CHECKING:
    from app.models.node import Node
    from app.models.user import User

class ActivatorType(str, Enum):
    """Tipi di attivatori fisici supportati."""
    NFC = "nfc"
    BLE = "ble"
    QR_CODE = "qr_code"
    CUSTOM = "custom"

class PhysicalActivator(SQLModel, table=True):
    """
    Modello per gli attivatori fisici (NFC, BLE, QR Code, etc.).
    Ogni attivatore è collegato a un nodo specifico e appartiene a un tenant.
    """
    
    __tablename__ = "physical_activators"
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    
    # Identificativo univoco dell'attivatore
    id: str = Field(primary_key=True, description="ID univoco dell'attivatore (es. seriale NFC)")
    type: ActivatorType = Field(description="Tipo di attivatore fisico")
    description: Optional[str] = Field(default=None, description="Descrizione dell'attivatore")
    
    # Collegamento al nodo e tenant
    linked_node_id: int = Field(foreign_key="nodes.id", description="ID del nodo collegato")
    tenant_id: uuid.UUID = Field(
        index=True,
        description="ID del tenant per isolamento logico multi-tenant"
    )
    
    # Stato dell'attivatore
    enabled: bool = Field(default=True, description="Indica se l'attivatore è attivo")
    
    # Metadati opzionali
    location: Optional[str] = Field(default=None, description="Posizione fisica dell'attivatore")
    installation_date: Optional[datetime] = Field(default=None, description="Data di installazione")
    last_maintenance: Optional[datetime] = Field(default=None, description="Data ultima manutenzione")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relazioni
    linked_node: Optional["Node"] = Relationship(back_populates="physical_activators")
    
    def __repr__(self) -> str:
        return f"<PhysicalActivator {self.id} ({self.type}) -> Node {self.linked_node_id}>"
    
    @property
    def is_active(self) -> bool:
        """Verifica se l'attivatore è attivo e abilitato."""
        return self.enabled
    
    @property
    def status_display(self) -> str:
        """Restituisce lo stato visualizzabile dell'attivatore."""
        if not self.enabled:
            return "Disabilitato"
        return "Attivo"
    
    def can_be_activated_by_user(self, user_tenant_id: uuid.UUID) -> bool:
        """
        Verifica se l'attivatore può essere attivato da un utente del tenant specificato.
        
        Args:
            user_tenant_id: ID del tenant dell'utente
            
        Returns:
            bool: True se l'attivatore può essere attivato
        """
        return (
            self.enabled and 
            self.tenant_id == user_tenant_id
        )
    
    def get_activation_context(self) -> dict:
        """
        Restituisce il contesto per l'attivazione dell'attivatore.
        
        Returns:
            dict: Contesto dell'attivazione
        """
        return {
            "activator_id": self.id,
            "activator_type": self.type,
            "node_id": self.linked_node_id,
            "tenant_id": str(self.tenant_id),
            "description": self.description,
            "location": self.location,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class PhysicalActivatorCreate(SQLModel):
    """Schema per la creazione di un nuovo attivatore fisico."""
    id: str = Field(description="ID univoco dell'attivatore")
    type: ActivatorType = Field(description="Tipo di attivatore")
    description: Optional[str] = None
    linked_node_id: int = Field(description="ID del nodo collegato")
    location: Optional[str] = None
    installation_date: Optional[datetime] = None

class PhysicalActivatorUpdate(SQLModel):
    """Schema per l'aggiornamento di un attivatore fisico."""
    description: Optional[str] = None
    enabled: Optional[bool] = None
    location: Optional[str] = None
    last_maintenance: Optional[datetime] = None

class PhysicalActivatorResponse(SQLModel):
    """Schema per la risposta degli attivatori fisici."""
    id: str
    type: ActivatorType
    description: Optional[str] = None
    linked_node_id: int
    tenant_id: uuid.UUID
    enabled: bool
    location: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    status_display: str
    
    # Informazioni del nodo collegato (se disponibili)
    node_name: Optional[str] = None
    node_description: Optional[str] = None

class ActivatorActivationRequest(SQLModel):
    """Schema per la richiesta di attivazione di un attivatore."""
    triggered_by: str = Field(default="manual", description="Chi ha attivato l'attivatore")
    metadata: Optional[dict] = Field(default=None, description="Metadati aggiuntivi dell'attivazione")

class ActivatorActivationResponse(SQLModel):
    """Schema per la risposta all'attivazione di un attivatore."""
    activator_id: str
    node_id: int
    tenant_id: uuid.UUID
    activation_successful: bool
    node_info: Optional[dict] = None
    available_actions: list[str] = Field(default_factory=list)
    message: str
    timestamp: datetime 