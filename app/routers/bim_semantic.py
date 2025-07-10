from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlmodel import Session, select
import uuid

from app.core.deps import get_current_user, get_session
from app.models.user import User
from app.models.bim_fragment import BIMFragment
from app.models.bim_model import BIMModel
from app.schemas.bim_fragment import (
    BIMFragmentRead, 
    BIMFragmentList, 
    BIMFragmentStats,
    BIMUploadResponse,
    BIMFragmentFilter
)
from app.services.bim_parser import get_bim_parser_service
from app.core.logging_config import get_logger
from app.utils.security import log_security_event

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/bim", tags=["BIM Semantic"])

@router.post("/semantic-upload", response_model=BIMUploadResponse)
async def upload_bim_semantic(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> BIMUploadResponse:
    """
    Carica un file BIM e ne estrae i frammenti semantici.
    
    Il file viene parsato per estrarre entità come stanze, impianti, oggetti strutturali
    e ogni entità viene associata automaticamente a un nodo Eterna.
    """
    import time
    start_time = time.time()
    
    logger.info(
        "Upload BIM semantico richiesto",
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        filename=file.filename,
        file_size=file.size
    )

    try:
        # Verifica autorizzazione
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non attivo"
            )

        # Ottieni servizio parser
        parser_service = get_bim_parser_service()
        
        # Parsa il file BIM
        bim_model, fragments = parser_service.parse_bim_file(
            file=file,
            tenant_id=current_user.tenant_id,
            house_id=1,  # TODO: Ottenere house_id dalla richiesta
            session=session
        )
        
        # Calcola statistiche
        nodes_created = sum(1 for f in fragments if f.node_id is not None)
        processing_time = time.time() - start_time
        
        logger.info(
            "Upload BIM semantico completato",
            user_id=current_user.id,
            bim_model_id=bim_model.id,
            fragments_count=len(fragments),
            nodes_created=nodes_created,
            processing_time=processing_time
        )

        # Log evento di sicurezza
        log_security_event(
            event="bim_semantic_upload",
            status="success",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            metadata={
                "bim_model_id": bim_model.id,
                "fragments_count": len(fragments),
                "nodes_created": nodes_created,
                "processing_time": processing_time,
                "filename": file.filename
            }
        )

        return BIMUploadResponse(
            bim_model_id=bim_model.id,
            fragments_count=len(fragments),
            nodes_created=nodes_created,
            processing_time=processing_time,
            message=f"File BIM processato con successo. Estratti {len(fragments)} frammenti semantici."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Errore durante upload BIM semantico: {e}",
            user_id=current_user.id,
            tenant_id=str(current_user.tenant_id)
        )
        
        log_security_event(
            event="bim_semantic_upload",
            status="failed",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            metadata={
                "error": str(e),
                "filename": file.filename
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il processing del file BIM: {str(e)}"
        )

@router.get("/fragments/{house_id}", response_model=BIMFragmentList)
async def get_bim_fragments(
    house_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Numero di pagina"),
    size: int = Query(50, ge=1, le=100, description="Dimensione pagina"),
    entity_type: Optional[str] = Query(None, description="Filtra per tipo di entità"),
    level: Optional[int] = Query(None, description="Filtra per livello"),
    min_area: Optional[float] = Query(None, description="Area minima"),
    max_area: Optional[float] = Query(None, description="Area massima"),
    has_node: Optional[bool] = Query(None, description="Filtra per presenza di nodo associato"),
    search: Optional[str] = Query(None, description="Ricerca nel nome dell'entità")
) -> BIMFragmentList:
    """
    Ottiene i frammenti BIM per una casa specifica.
    
    I frammenti sono filtrati per tenant e house per garantire l'isolamento dei dati.
    Supporta paginazione e filtri avanzati.
    """
    logger.info(
        "Richiesta frammenti BIM",
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        house_id=house_id,
        page=page,
        size=size
    )

    try:
        # Verifica autorizzazione
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non attivo"
            )

        # Costruisci query base
        query = select(BIMFragment).where(
            BIMFragment.tenant_id == current_user.tenant_id,
            BIMFragment.house_id == house_id
        )

        # Applica filtri
        if entity_type:
            query = query.where(BIMFragment.entity_type == entity_type)
        
        if level is not None:
            query = query.where(BIMFragment.level == level)
        
        if min_area is not None:
            query = query.where(BIMFragment.area >= min_area)
        
        if max_area is not None:
            query = query.where(BIMFragment.area <= max_area)
        
        if has_node is not None:
            if has_node:
                query = query.where(BIMFragment.node_id.is_not(None))
            else:
                query = query.where(BIMFragment.node_id.is_(None))
        
        if search:
            query = query.where(BIMFragment.entity_name.ilike(f"%{search}%"))

        # Conta totale risultati
        total_query = select(BIMFragment).where(
            BIMFragment.tenant_id == current_user.tenant_id,
            BIMFragment.house_id == house_id
        )
        total = len(session.exec(total_query).all())

        # Applica paginazione
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # Esegui query
        fragments = session.exec(query).all()

        # Converti in schema di risposta
        fragment_reads = []
        for fragment in fragments:
            fragment_read = BIMFragmentRead(
                id=fragment.id,
                tenant_id=fragment.tenant_id,
                house_id=fragment.house_id,
                bim_model_id=fragment.bim_model_id,
                node_id=fragment.node_id,
                entity_type=fragment.entity_type,
                entity_name=fragment.entity_name,
                area=fragment.area,
                volume=fragment.volume,
                level=fragment.level,
                ifc_guid=fragment.ifc_guid,
                bounding_box=fragment.bounding_box,
                metadata=fragment.metadata,
                created_at=fragment.created_at,
                updated_at=fragment.updated_at,
                display_name=fragment.display_name,
                has_geometry=fragment.has_geometry,
                dimensions=fragment.dimensions
            )
            fragment_reads.append(fragment_read)

        logger.info(
            "Frammenti BIM restituiti",
            user_id=current_user.id,
            house_id=house_id,
            fragments_count=len(fragment_reads),
            total=total
        )

        return BIMFragmentList(
            fragments=fragment_reads,
            total=total,
            page=page,
            size=size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Errore durante recupero frammenti BIM: {e}",
            user_id=current_user.id,
            house_id=house_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei frammenti BIM: {str(e)}"
        )

@router.get("/fragments/{house_id}/stats", response_model=BIMFragmentStats)
async def get_bim_fragments_stats(
    house_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> BIMFragmentStats:
    """
    Ottiene le statistiche dei frammenti BIM per una casa specifica.
    """
    logger.info(
        "Richiesta statistiche frammenti BIM",
        user_id=current_user.id,
        house_id=house_id
    )

    try:
        # Verifica autorizzazione
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non attivo"
            )

        # Query base
        query = select(BIMFragment).where(
            BIMFragment.tenant_id == current_user.tenant_id,
            BIMFragment.house_id == house_id
        )
        
        fragments = session.exec(query).all()

        # Calcola statistiche
        total_fragments = len(fragments)
        fragments_by_type = {}
        total_area = 0.0
        total_volume = 0.0
        levels = set()

        for fragment in fragments:
            # Conta per tipo
            entity_type = fragment.entity_type
            fragments_by_type[entity_type] = fragments_by_type.get(entity_type, 0) + 1
            
            # Somma aree e volumi
            if fragment.area:
                total_area += fragment.area
            if fragment.volume:
                total_volume += fragment.volume
            
            # Raccogli livelli
            if fragment.level is not None:
                levels.add(fragment.level)

        logger.info(
            "Statistiche frammenti BIM calcolate",
            user_id=current_user.id,
            house_id=house_id,
            total_fragments=total_fragments
        )

        return BIMFragmentStats(
            total_fragments=total_fragments,
            fragments_by_type=fragments_by_type,
            total_area=total_area,
            total_volume=total_volume,
            levels=sorted(list(levels))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Errore durante calcolo statistiche BIM: {e}",
            user_id=current_user.id,
            house_id=house_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il calcolo delle statistiche: {str(e)}"
        )

@router.get("/fragments/{house_id}/{fragment_id}", response_model=BIMFragmentRead)
async def get_bim_fragment(
    house_id: int,
    fragment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> BIMFragmentRead:
    """
    Ottiene un singolo frammento BIM per ID.
    """
    logger.info(
        "Richiesta frammento BIM specifico",
        user_id=current_user.id,
        house_id=house_id,
        fragment_id=fragment_id
    )

    try:
        # Verifica autorizzazione
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non attivo"
            )

        # Cerca frammento
        query = select(BIMFragment).where(
            BIMFragment.id == fragment_id,
            BIMFragment.tenant_id == current_user.tenant_id,
            BIMFragment.house_id == house_id
        )
        
        fragment = session.exec(query).first()
        
        if not fragment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frammento BIM non trovato"
            )

        return BIMFragmentRead(
            id=fragment.id,
            tenant_id=fragment.tenant_id,
            house_id=fragment.house_id,
            bim_model_id=fragment.bim_model_id,
            node_id=fragment.node_id,
            entity_type=fragment.entity_type,
            entity_name=fragment.entity_name,
            area=fragment.area,
            volume=fragment.volume,
            level=fragment.level,
            ifc_guid=fragment.ifc_guid,
            bounding_box=fragment.bounding_box,
            metadata=fragment.metadata,
            created_at=fragment.created_at,
            updated_at=fragment.updated_at,
            display_name=fragment.display_name,
            has_geometry=fragment.has_geometry,
            dimensions=fragment.dimensions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Errore durante recupero frammento BIM: {e}",
            user_id=current_user.id,
            fragment_id=fragment_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero del frammento BIM: {str(e)}"
        )

@router.delete("/fragments/{house_id}/{fragment_id}")
async def delete_bim_fragment(
    house_id: int,
    fragment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> dict:
    """
    Elimina un frammento BIM specifico.
    """
    logger.info(
        "Richiesta eliminazione frammento BIM",
        user_id=current_user.id,
        house_id=house_id,
        fragment_id=fragment_id
    )

    try:
        # Verifica autorizzazione
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non attivo"
            )

        # Cerca frammento
        query = select(BIMFragment).where(
            BIMFragment.id == fragment_id,
            BIMFragment.tenant_id == current_user.tenant_id,
            BIMFragment.house_id == house_id
        )
        
        fragment = session.exec(query).first()
        
        if not fragment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frammento BIM non trovato"
            )

        # Elimina frammento
        session.delete(fragment)
        session.commit()

        logger.info(
            "Frammento BIM eliminato",
            user_id=current_user.id,
            fragment_id=fragment_id
        )

        log_security_event(
            event="bim_fragment_delete",
            status="success",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            metadata={
                "fragment_id": fragment_id,
                "house_id": house_id,
                "entity_name": fragment.entity_name
            }
        )

        return {"message": "Frammento BIM eliminato con successo"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Errore durante eliminazione frammento BIM: {e}",
            user_id=current_user.id,
            fragment_id=fragment_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'eliminazione del frammento BIM: {str(e)}"
        ) 