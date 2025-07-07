"""
Router per la gestione degli attivatori fisici con supporto multi-tenant.
Gestisce NFC, BLE, QR Code e altri attivatori fisici collegati ai nodi.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
import uuid
from datetime import datetime, timezone

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    get_session
)
from app.core.auth.rbac import require_permission_in_tenant
from app.models.user import User
from app.models.node import Node
from app.models.physical_activator import (
    PhysicalActivator,
    ActivatorType,
    PhysicalActivatorCreate,
    PhysicalActivatorUpdate,
    PhysicalActivatorResponse,
    ActivatorActivationRequest,
    ActivatorActivationResponse
)
from app.core.logging_multi_tenant import (
    multi_tenant_logger,
    log_security_violation
)
from app.db.utils import safe_exec

router = APIRouter(prefix="/api/v1/activator", tags=["Physical Activators"])

@router.post("/", response_model=PhysicalActivatorResponse)
async def create_physical_activator(
    activator_data: PhysicalActivatorCreate,
    current_user: User = Depends(require_permission_in_tenant("manage_activators")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Crea un nuovo attivatore fisico.
    Richiede permesso 'manage_activators' nel tenant attivo.
    """
    try:
        # Verifica che il nodo esista e appartenga al tenant
        node_query = select(Node).where(
            Node.id == activator_data.linked_node_id,
            Node.tenant_id == tenant_id
        )
        node = safe_exec(session, node_query).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nodo non trovato o non appartiene al tenant corrente"
            )
        
        # Verifica che l'ID dell'attivatore non esista già
        existing_activator = safe_exec(
            session, 
            select(PhysicalActivator).where(PhysicalActivator.id == activator_data.id)
        ).first()
        
        if existing_activator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attivatore con questo ID esiste già"
            )
        
        # Crea l'attivatore
        activator = PhysicalActivator(
            **activator_data.dict(),
            tenant_id=tenant_id
        )
        
        session.add(activator)
        session.commit()
        session.refresh(activator)
        
        # Log della creazione
        multi_tenant_logger.info(
            f"Attivatore fisico creato: {activator.id}",
            {
                "event": "activator_created",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator.id,
                "activator_type": activator.type,
                "node_id": activator.linked_node_id
            }
        )
        
        return PhysicalActivatorResponse.from_orm(activator)
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante creazione attivatore: {e}",
            {
                "event": "activator_creation_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la creazione dell'attivatore"
        )

@router.get("/", response_model=List[PhysicalActivatorResponse])
async def get_physical_activators(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(10, ge=1, le=100, description="Numero massimo di record"),
    activator_type: Optional[ActivatorType] = Query(None, description="Filtra per tipo di attivatore"),
    enabled: Optional[bool] = Query(None, description="Filtra per stato abilitato"),
    current_user: User = Depends(require_permission_in_tenant("read_activators")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene la lista degli attivatori fisici del tenant corrente.
    Richiede permesso 'read_activators' nel tenant attivo.
    """
    try:
        # Query base filtrata per tenant
        query = select(PhysicalActivator).where(PhysicalActivator.tenant_id == tenant_id)
        
        # Filtri opzionali
        if activator_type:
            query = query.where(PhysicalActivator.type == activator_type)
        
        if enabled is not None:
            query = query.where(PhysicalActivator.enabled == enabled)
        
        # Paginazione
        query = query.offset(skip).limit(limit)
        
        activators = safe_exec(session, query).all()
        
        # Log dell'accesso
        multi_tenant_logger.info(
            f"Accesso lista attivatori - {len(activators)} attivatori recuperati",
            {
                "event": "activators_list_access",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activators_count": len(activators)
            }
        )
        
        return [PhysicalActivatorResponse.from_orm(activator) for activator in activators]
        
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante recupero attivatori: {e}",
            {
                "event": "activators_list_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero degli attivatori"
        )

@router.get("/{activator_id}", response_model=PhysicalActivatorResponse)
async def get_physical_activator(
    activator_id: str,
    current_user: User = Depends(require_permission_in_tenant("read_activators")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Ottiene un attivatore fisico specifico del tenant corrente.
    Richiede permesso 'read_activators' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(PhysicalActivator).where(
            PhysicalActivator.id == activator_id,
            PhysicalActivator.tenant_id == tenant_id
        )
        
        activator = safe_exec(session, query).first()
        
        if not activator:
            # Log tentativo di accesso non autorizzato
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="unauthorized_activator_access",
                details=f"Tentativo di accesso ad attivatore {activator_id} non esistente nel tenant"
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attivatore non trovato"
            )
        
        # Log dell'accesso
        multi_tenant_logger.info(
            f"Accesso attivatore {activator_id}",
            {
                "event": "activator_access",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        
        return PhysicalActivatorResponse.from_orm(activator)
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante recupero attivatore: {e}",
            {
                "event": "activator_access_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dell'attivatore"
        )

@router.put("/{activator_id}", response_model=PhysicalActivatorResponse)
async def update_physical_activator(
    activator_id: str,
    activator_update: PhysicalActivatorUpdate,
    current_user: User = Depends(require_permission_in_tenant("manage_activators")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un attivatore fisico del tenant corrente.
    Richiede permesso 'manage_activators' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(PhysicalActivator).where(
            PhysicalActivator.id == activator_id,
            PhysicalActivator.tenant_id == tenant_id
        )
        
        activator = safe_exec(session, query).first()
        
        if not activator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attivatore non trovato"
            )
        
        # Aggiorna i campi
        update_data = activator_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activator, field, value)
        
        activator.updated_at = datetime.now(timezone.utc)
        session.add(activator)
        session.commit()
        session.refresh(activator)
        
        # Log dell'aggiornamento
        multi_tenant_logger.info(
            f"Attivatore aggiornato: {activator_id}",
            {
                "event": "activator_updated",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id,
                "updated_fields": list(update_data.keys())
            }
        )
        
        return PhysicalActivatorResponse.from_orm(activator)
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante aggiornamento attivatore: {e}",
            {
                "event": "activator_update_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'aggiornamento dell'attivatore"
        )

@router.delete("/{activator_id}")
async def delete_physical_activator(
    activator_id: str,
    current_user: User = Depends(require_permission_in_tenant("manage_activators")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Elimina un attivatore fisico del tenant corrente.
    Richiede permesso 'manage_activators' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(PhysicalActivator).where(
            PhysicalActivator.id == activator_id,
            PhysicalActivator.tenant_id == tenant_id
        )
        
        activator = safe_exec(session, query).first()
        
        if not activator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attivatore non trovato"
            )
        
        # Elimina l'attivatore
        session.delete(activator)
        session.commit()
        
        # Log dell'eliminazione
        multi_tenant_logger.info(
            f"Attivatore eliminato: {activator_id}",
            {
                "event": "activator_deleted",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        
        return {"message": "Attivatore eliminato con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante eliminazione attivatore: {e}",
            {
                "event": "activator_delete_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'eliminazione dell'attivatore"
        )

@router.post("/{activator_id}/activate", response_model=ActivatorActivationResponse)
async def activate_physical_activator(
    activator_id: str,
    activation_request: ActivatorActivationRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Attiva un attivatore fisico.
    Non richiede permessi specifici ma verifica che l'utente appartenga al tenant dell'attivatore.
    """
    try:
        # Recupera l'attivatore
        query = select(PhysicalActivator).where(PhysicalActivator.id == activator_id)
        activator = safe_exec(session, query).first()
        
        if not activator:
            # Log tentativo di attivazione non autorizzata
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="unauthorized_activator_activation",
                details=f"Tentativo di attivazione attivatore {activator_id} non esistente"
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attivatore non trovato"
            )
        
        # Verifica che l'attivatore sia abilitato
        if not activator.enabled:
            # Log tentativo di attivazione di attivatore disabilitato
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="disabled_activator_activation",
                details=f"Tentativo di attivazione attivatore {activator_id} disabilitato"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Attivatore disabilitato"
            )
        
        # Verifica che l'attivatore appartenga al tenant dell'utente
        if activator.tenant_id != tenant_id:
            # Log tentativo di attivazione cross-tenant
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="cross_tenant_activator_activation",
                details=f"Tentativo di attivazione attivatore {activator_id} di tenant diverso"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accesso negato all'attivatore"
            )
        
        # Recupera il nodo collegato
        node_query = select(Node).where(Node.id == activator.linked_node_id)
        node = safe_exec(session, node_query).first()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nodo collegato non trovato"
            )
        
        # Prepara le informazioni del nodo
        node_info = {
            "id": node.id,
            "name": node.name,
            "description": node.description,
            "nfc_id": node.nfc_id,
            "location": f"House {node.house_id}"
        }
        
        # Determina le azioni disponibili basate sul tipo di nodo
        available_actions = ["view_documents", "view_maintenance", "view_bim_models"]
        if node.is_master_node:
            available_actions.append("manage_area")
        
        # Log dell'attivazione
        multi_tenant_logger.info(
            f"Attivatore attivato: {activator_id}",
            {
                "event": "activator_activated",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id,
                "node_id": node.id,
                "triggered_by": activation_request.triggered_by,
                "meta_data": activation_request.meta_data
            }
        )
        
        return ActivatorActivationResponse(
            activator_id=activator_id,
            node_id=node.id,
            tenant_id=tenant_id,
            activation_successful=True,
            node_info=node_info,
            available_actions=available_actions,
            message=f"Attivatore {activator.description or activator_id} attivato con successo",
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante attivazione attivatore: {e}",
            {
                "event": "activator_activation_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "activator_id": activator_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'attivazione dell'attivatore"
        ) 