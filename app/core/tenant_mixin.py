"""
Mixin per centralizzare la logica del filtraggio multi-tenant.
Fornisce metodi utility per applicare automaticamente i filtri tenant_id
nelle operazioni CRUD.
"""

from typing import TypeVar, Type, List, Optional, Any
from sqlmodel import Session, select, SQLModel
from fastapi import HTTPException, status
import uuid

T = TypeVar('T', bound=SQLModel)

class TenantMixin:
    """
    Mixin per aggiungere funzionalità multi-tenant ai modelli.
    
    Questo mixin fornisce metodi utility per:
    - Filtrare query per tenant_id
    - Verificare l'accesso a risorse specifiche
    - Assegnare automaticamente tenant_id durante la creazione
    """
    
    @classmethod
    def filter_by_tenant(
        cls: Type[T],
        session: Session,
        tenant_id: uuid.UUID,
        **filters
    ) -> List[T]:
        """
        Filtra i record per tenant_id e altri filtri opzionali.
        
        Args:
            session: Sessione del database
            tenant_id: ID del tenant per il filtraggio
            **filters: Filtri aggiuntivi da applicare
            
        Returns:
            Lista di record filtrati per tenant_id
        """
        query = select(cls).where(cls.tenant_id == tenant_id)
        
        # Applica filtri aggiuntivi
        for field, value in filters.items():
            if hasattr(cls, field) and value is not None:
                query = query.where(getattr(cls, field) == value)
        
        result = session.exec(query)
        return list(result.all())
    
    @classmethod
    def get_by_id_and_tenant(
        cls: Type[T],
        session: Session,
        item_id: int,
        tenant_id: uuid.UUID
    ) -> Optional[T]:
        """
        Ottiene un record specifico verificando che appartenga al tenant.
        
        Args:
            session: Sessione del database
            item_id: ID del record da recuperare
            tenant_id: ID del tenant per la verifica
            
        Returns:
            Record se trovato e appartiene al tenant, None altrimenti
        """
        query = select(cls).where(
            cls.id == item_id,
            cls.tenant_id == tenant_id
        )
        result = session.exec(query)
        return result.first()
    
    @classmethod
    def create_with_tenant(
        cls: Type[T],
        session: Session,
        tenant_id: uuid.UUID,
        **data
    ) -> T:
        """
        Crea un nuovo record assegnando automaticamente il tenant_id.
        
        Args:
            session: Sessione del database
            tenant_id: ID del tenant da assegnare
            **data: Dati per la creazione del record
            
        Returns:
            Record creato con tenant_id assegnato
        """
        # Assegna automaticamente il tenant_id
        data['tenant_id'] = tenant_id
        
        # Crea l'istanza del modello
        instance = cls(**data)
        session.add(instance)
        session.commit()
        session.refresh(instance)
        
        return instance
    
    @classmethod
    def update_with_tenant_check(
        cls: Type[T],
        session: Session,
        item_id: int,
        tenant_id: uuid.UUID,
        **update_data
    ) -> Optional[T]:
        """
        Aggiorna un record verificando che appartenga al tenant.
        
        Args:
            session: Sessione del database
            item_id: ID del record da aggiornare
            tenant_id: ID del tenant per la verifica
            **update_data: Dati da aggiornare
            
        Returns:
            Record aggiornato se trovato e appartiene al tenant, None altrimenti
        """
        # Verifica che il record esista e appartenga al tenant
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
    def delete_with_tenant_check(
        cls: Type[T],
        session: Session,
        item_id: int,
        tenant_id: uuid.UUID
    ) -> bool:
        """
        Elimina un record verificando che appartenga al tenant.
        
        Args:
            session: Sessione del database
            item_id: ID del record da eliminare
            tenant_id: ID del tenant per la verifica
            
        Returns:
            True se eliminato con successo, False altrimenti
        """
        # Verifica che il record esista e appartenga al tenant
        item = cls.get_by_id_and_tenant(session, item_id, tenant_id)
        if not item:
            return False
        
        session.delete(item)
        session.commit()
        return True
    
    @classmethod
    def count_by_tenant(
        cls: Type[T],
        session: Session,
        tenant_id: uuid.UUID,
        **filters
    ) -> int:
        """
        Conta i record per tenant_id e altri filtri opzionali.
        
        Args:
            session: Sessione del database
            tenant_id: ID del tenant per il filtraggio
            **filters: Filtri aggiuntivi da applicare
            
        Returns:
            Numero di record che soddisfano i criteri
        """
        query = select(cls).where(cls.tenant_id == tenant_id)
        
        # Applica filtri aggiuntivi
        for field, value in filters.items():
            if hasattr(cls, field) and value is not None:
                query = query.where(getattr(cls, field) == value)
        
        result = session.exec(query)
        return len(list(result.all()))
    
    @classmethod
    def exists_in_tenant(
        cls: Type[T],
        session: Session,
        item_id: int,
        tenant_id: uuid.UUID
    ) -> bool:
        """
        Verifica se un record esiste e appartiene al tenant.
        
        Args:
            session: Sessione del database
            item_id: ID del record da verificare
            tenant_id: ID del tenant per la verifica
            
        Returns:
            True se il record esiste e appartiene al tenant, False altrimenti
        """
        return cls.get_by_id_and_tenant(session, item_id, tenant_id) is not None

def apply_tenant_filter(query, tenant_id: uuid.UUID):
    """
    Utility per applicare il filtro tenant_id a una query SQLModel generica.
    
    Args:
        query: Query SQLModel da filtrare
        tenant_id: UUID del tenant per il filtraggio
        
    Returns:
        Query filtrata per tenant_id
    """
    # Verifica se il modello ha il campo tenant_id
    if hasattr(query.column_descriptions[0]['entity'], 'tenant_id'):
        return query.filter(query.column_descriptions[0]['entity'].tenant_id == tenant_id)
    return query

def ensure_tenant_access(
    session: Session,
    model_class: Type[T],
    item_id: int,
    tenant_id: uuid.UUID
) -> T:
    """
    Utility per verificare l'accesso a una risorsa specifica del tenant.
    
    Args:
        session: Sessione del database
        model_class: Classe del modello da verificare
        item_id: ID del record da verificare
        tenant_id: ID del tenant per la verifica
        
    Returns:
        Record se accesso consentito
        
    Raises:
        HTTPException: Se l'accesso è negato
    """
    query = select(model_class).where(
        model_class.id == item_id,
        model_class.tenant_id == tenant_id
    )
    result = session.exec(query)
    item = result.first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found or access denied"
        )
    
    return item 