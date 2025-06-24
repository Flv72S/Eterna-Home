"""
Modello per le interazioni con l'assistente AI con supporto multi-tenant.
Gestisce l'isolamento completo delle interazioni per tenant.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
import uuid

class AIAssistantInteraction(SQLModel, table=True):
    """
    Modello per le interazioni con l'assistente AI.
    Ogni interazione è isolata per tenant e utente.
    """
    
    __tablename__ = "ai_interactions"
    
    id: int = Field(default=None, primary_key=True)
    tenant_id: uuid.UUID = Field(index=True, nullable=False)
    user_id: int = Field(index=True, nullable=False)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Contenuto dell'interazione
    prompt: str = Field(nullable=False)
    response: str = Field(nullable=False)
    
    # Metadati opzionali
    context: Optional[Dict[str, Any]] = Field(default=None, sa_column_kwargs={"type": "JSON"})
    session_id: Optional[str] = Field(default=None, index=True)
    interaction_type: Optional[str] = Field(default="chat")  # chat, query, analysis, etc.
    
    # Statistiche
    prompt_tokens: Optional[int] = Field(default=None)
    response_tokens: Optional[int] = Field(default=None)
    total_tokens: Optional[int] = Field(default=None)
    
    # Stato dell'interazione
    status: str = Field(default="completed")  # pending, completed, failed, cancelled
    error_message: Optional[str] = Field(default=None)
    
    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True

class AIInteractionCreate(SQLModel):
    """Schema per la creazione di una nuova interazione AI."""
    prompt: str
    response: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    interaction_type: Optional[str] = "chat"
    prompt_tokens: Optional[int] = None
    response_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    status: str = "completed"
    error_message: Optional[str] = None

class AIInteractionResponse(SQLModel):
    """Schema per la risposta delle interazioni AI."""
    id: int
    tenant_id: uuid.UUID
    user_id: int
    timestamp: datetime
    prompt: str
    response: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    interaction_type: str
    prompt_tokens: Optional[int] = None
    response_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AIInteractionList(SQLModel):
    """Schema per la lista delle interazioni AI."""
    items: list[AIInteractionResponse]
    total: int
    page: int
    size: int
    pages: int 