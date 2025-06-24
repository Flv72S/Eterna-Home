"""
Router per l'assistente AI con supporto multi-tenant.
Gestisce le interazioni AI con isolamento completo per tenant.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select, func
import uuid
from datetime import datetime, timezone

from app.core.deps import (
    get_current_user, 
    get_current_tenant,
    require_permission_in_tenant,
    get_session
)
from app.models.user import User
from app.models.ai_interaction import (
    AIAssistantInteraction,
    AIInteractionCreate,
    AIInteractionResponse,
    AIInteractionList
)
from app.core.logging_multi_tenant import (
    multi_tenant_logger,
    log_ai_usage,
    log_security_violation
)
from app.db.utils import safe_exec

router = APIRouter(prefix="/api/v1/ai", tags=["AI Assistant"])

@router.post("/chat", response_model=AIInteractionResponse)
async def chat_with_ai(
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_permission_in_tenant("ai_access")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Chat con l'assistente AI.
    Richiede permesso 'ai_access' nel tenant attivo.
    """
    try:
        # Simula risposta AI (in produzione qui ci sarebbe l'integrazione con l'AI)
        ai_response = f"Risposta AI per: {prompt[:50]}..."
        
        # Calcola token (simulato)
        prompt_tokens = len(prompt.split())
        response_tokens = len(ai_response.split())
        total_tokens = prompt_tokens + response_tokens
        
        # Crea l'interazione AI
        interaction_data = AIInteractionCreate(
            prompt=prompt,
            response=ai_response,
            context=context,
            session_id=session_id,
            interaction_type="chat",
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            total_tokens=total_tokens,
            status="completed"
        )
        
        # Salva nel database
        interaction = AIAssistantInteraction(
            **interaction_data.dict(),
            tenant_id=tenant_id,
            user_id=current_user.id
        )
        
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        # Log dell'interazione
        log_ai_usage(
            user_id=current_user.id,
            tenant_id=tenant_id,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            metadata={
                "interaction_id": interaction.id,
                "session_id": session_id,
                "context": context
            }
        )
        
        return AIInteractionResponse.from_orm(interaction)
        
    except Exception as e:
        # Log dell'errore
        multi_tenant_logger.error(
            f"Errore durante chat AI: {e}",
            {
                "event": "ai_chat_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "prompt_length": len(prompt)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la comunicazione con l'AI"
        )

@router.get("/history", response_model=AIInteractionList)
async def get_ai_history(
    skip: int = 0,
    limit: int = 50,
    session_id: Optional[str] = None,
    interaction_type: Optional[str] = None,
    current_user: User = Depends(require_permission_in_tenant("ai_access")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Ottiene la cronologia delle interazioni AI del tenant corrente.
    Richiede permesso 'ai_access' nel tenant attivo.
    """
    try:
        # Query base filtrata per tenant
        base_query = select(AIAssistantInteraction).where(
            AIAssistantInteraction.tenant_id == tenant_id
        )
        
        # Filtri opzionali
        if session_id:
            base_query = base_query.where(AIAssistantInteraction.session_id == session_id)
        
        if interaction_type:
            base_query = base_query.where(AIAssistantInteraction.interaction_type == interaction_type)
        
        # Query per contare totale
        total_query = select(func.count(AIAssistantInteraction.id)).where(
            AIAssistantInteraction.tenant_id == tenant_id
        )
        
        if session_id:
            total_query = total_query.where(AIAssistantInteraction.session_id == session_id)
        
        if interaction_type:
            total_query = total_query.where(AIAssistantInteraction.interaction_type == interaction_type)
        
        total = safe_exec(db, total_query).first()
        
        # Query per lista con paginazione
        query = (
            base_query
            .order_by(AIAssistantInteraction.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        
        interactions = safe_exec(db, query).all()
        
        # Log dell'accesso alla cronologia
        multi_tenant_logger.info(
            f"Accesso cronologia AI - {len(interactions)} interazioni recuperate",
            {
                "event": "ai_history_access",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "interactions_count": len(interactions),
                "session_id": session_id
            }
        )
        
        return AIInteractionList(
            items=[AIInteractionResponse.from_orm(interaction) for interaction in interactions],
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante recupero cronologia AI: {e}",
            {
                "event": "ai_history_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della cronologia AI"
        )

@router.get("/history/{interaction_id}", response_model=AIInteractionResponse)
async def get_ai_interaction(
    interaction_id: int,
    current_user: User = Depends(require_permission_in_tenant("ai_access")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Ottiene una specifica interazione AI del tenant corrente.
    Richiede permesso 'ai_access' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(AIAssistantInteraction).where(
            AIAssistantInteraction.id == interaction_id,
            AIAssistantInteraction.tenant_id == tenant_id
        )
        
        interaction = safe_exec(db, query).first()
        
        if not interaction:
            # Log tentativo di accesso non autorizzato
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="unauthorized_ai_access",
                details=f"Tentativo di accesso a interazione AI {interaction_id} non esistente nel tenant"
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interazione AI non trovata"
            )
        
        # Log dell'accesso all'interazione
        multi_tenant_logger.info(
            f"Accesso interazione AI {interaction_id}",
            {
                "event": "ai_interaction_access",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "interaction_id": interaction_id
            }
        )
        
        return AIInteractionResponse.from_orm(interaction)
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante recupero interazione AI: {e}",
            {
                "event": "ai_interaction_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "interaction_id": interaction_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dell'interazione AI"
        )

@router.delete("/history/{interaction_id}")
async def delete_ai_interaction(
    interaction_id: int,
    current_user: User = Depends(require_permission_in_tenant("ai_manage")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Elimina una specifica interazione AI del tenant corrente.
    Richiede permesso 'ai_manage' nel tenant attivo.
    """
    try:
        # Query filtrata per tenant e ID
        query = select(AIAssistantInteraction).where(
            AIAssistantInteraction.id == interaction_id,
            AIAssistantInteraction.tenant_id == tenant_id
        )
        
        interaction = safe_exec(db, query).first()
        
        if not interaction:
            # Log tentativo di eliminazione non autorizzata
            log_security_violation(
                user_id=current_user.id,
                tenant_id=tenant_id,
                violation_type="unauthorized_ai_delete",
                details=f"Tentativo di eliminazione interazione AI {interaction_id} non esistente nel tenant"
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interazione AI non trovata"
            )
        
        # Elimina l'interazione
        db.delete(interaction)
        db.commit()
        
        # Log dell'eliminazione
        multi_tenant_logger.info(
            f"Eliminazione interazione AI {interaction_id}",
            {
                "event": "ai_interaction_delete",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "interaction_id": interaction_id
            }
        )
        
        return {"message": "Interazione AI eliminata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante eliminazione interazione AI: {e}",
            {
                "event": "ai_interaction_delete_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "interaction_id": interaction_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'eliminazione dell'interazione AI"
        )

@router.get("/stats")
async def get_ai_stats(
    current_user: User = Depends(require_permission_in_tenant("ai_access")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Ottiene statistiche delle interazioni AI del tenant corrente.
    Richiede permesso 'ai_access' nel tenant attivo.
    """
    try:
        # Statistiche per tenant
        total_interactions_query = select(func.count(AIAssistantInteraction.id)).where(
            AIAssistantInteraction.tenant_id == tenant_id
        )
        total_interactions = safe_exec(db, total_interactions_query).first()
        
        # Token totali
        total_tokens_query = select(func.sum(AIAssistantInteraction.total_tokens)).where(
            AIAssistantInteraction.tenant_id == tenant_id
        )
        total_tokens = safe_exec(db, total_tokens_query).first() or 0
        
        # Interazioni per tipo
        type_stats_query = select(
            AIAssistantInteraction.interaction_type,
            func.count(AIAssistantInteraction.id)
        ).where(
            AIAssistantInteraction.tenant_id == tenant_id
        ).group_by(AIAssistantInteraction.interaction_type)
        
        type_stats = safe_exec(db, type_stats_query).all()
        
        # Interazioni per utente
        user_stats_query = select(
            AIAssistantInteraction.user_id,
            func.count(AIAssistantInteraction.id)
        ).where(
            AIAssistantInteraction.tenant_id == tenant_id
        ).group_by(AIAssistantInteraction.user_id)
        
        user_stats = safe_exec(db, user_stats_query).all()
        
        # Log dell'accesso alle statistiche
        multi_tenant_logger.info(
            f"Accesso statistiche AI - {total_interactions} interazioni totali",
            {
                "event": "ai_stats_access",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "total_interactions": total_interactions,
                "total_tokens": total_tokens
            }
        )
        
        return {
            "tenant_id": str(tenant_id),
            "total_interactions": total_interactions,
            "total_tokens": total_tokens,
            "type_distribution": [
                {"type": interaction_type, "count": count} 
                for interaction_type, count in type_stats
            ],
            "user_distribution": [
                {"user_id": user_id, "count": count} 
                for user_id, count in user_stats
            ]
        }
        
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante recupero statistiche AI: {e}",
            {
                "event": "ai_stats_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche AI"
        )

@router.post("/analyze-document")
async def analyze_document_with_ai(
    document_id: int,
    analysis_type: str = "general",
    current_user: User = Depends(require_permission_in_tenant("ai_access")),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: Session = Depends(get_session)
):
    """
    Analizza un documento con l'AI.
    Richiede permesso 'ai_access' nel tenant attivo.
    """
    try:
        # Simula analisi AI del documento
        analysis_result = f"Analisi {analysis_type} del documento {document_id}: Contenuto analizzato..."
        
        # Crea l'interazione AI per l'analisi
        interaction_data = AIInteractionCreate(
            prompt=f"Analizza documento {document_id} con tipo {analysis_type}",
            response=analysis_result,
            context={
                "document_id": document_id,
                "analysis_type": analysis_type,
                "operation": "document_analysis"
            },
            interaction_type="analysis",
            prompt_tokens=10,
            response_tokens=50,
            total_tokens=60,
            status="completed"
        )
        
        # Salva nel database
        interaction = AIAssistantInteraction(
            **interaction_data.dict(),
            tenant_id=tenant_id,
            user_id=current_user.id
        )
        
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        # Log dell'analisi
        multi_tenant_logger.info(
            f"Analisi documento {document_id} con AI",
            {
                "event": "ai_document_analysis",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "document_id": document_id,
                "analysis_type": analysis_type,
                "interaction_id": interaction.id
            }
        )
        
        return {
            "analysis_result": analysis_result,
            "interaction_id": interaction.id,
            "document_id": document_id,
            "analysis_type": analysis_type
        }
        
    except Exception as e:
        multi_tenant_logger.error(
            f"Errore durante analisi documento AI: {e}",
            {
                "event": "ai_document_analysis_error",
                "user_id": current_user.id,
                "tenant_id": str(tenant_id),
                "document_id": document_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante l'analisi del documento"
        )

# TODO: Implementare endpoint per export cronologia AI
# TODO: Aggiungere endpoint per configurazione AI per tenant
# TODO: Implementare rate limiting per interazioni AI
# TODO: Aggiungere endpoint per feedback sulle risposte AI 