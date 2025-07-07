from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user, get_current_tenant, get_db
from app.core.auth.rbac import require_role_in_tenant, require_permission_in_tenant
from app.models.user import User
from app.schemas.user_house import (
    UserHouseCreate,
    UserHouseUpdate,
    UserHouseResponse,
    UserHouseList,
    HouseAccessRequest,
    HouseAccessResponse,
    UserHouseSummary
)
from app.services.user_house import UserHouseService
from app.core.logging_multi_tenant import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/user-house", tags=["user-house"])

@router.get("/", response_model=UserHouseList)
async def get_user_houses(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(require_permission_in_tenant("manage_house_access")),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filtra per ID utente"),
    house_id: Optional[int] = Query(None, description="Filtra per ID casa"),
    page: int = Query(1, ge=1, description="Numero pagina"),
    size: int = Query(50, ge=1, le=100, description="Dimensione pagina")
):
    """
    Recupera le associazioni utente-casa.
    Richiede il permesso 'manage_house_access' nel tenant.
    """
    try:
        service = UserHouseService(db)
        result = service.get_user_houses(
            current_user=current_user,
            tenant_id=tenant_id,
            user_id=user_id,
            house_id=house_id,
            page=page,
            size=size
        )
        
        logger.info(
            "Lista associazioni utente-casa recuperata",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "total": result.total,
                "page": page,
                "size": size
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero lista associazioni: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.post("/", response_model=UserHouseResponse)
async def create_user_house(
    user_house_data: UserHouseCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(require_permission_in_tenant("manage_house_access")),
    db: Session = Depends(get_db)
):
    """
    Crea una nuova associazione utente-casa.
    Richiede il permesso 'manage_house_access' nel tenant.
    """
    try:
        user_house_data.tenant_id = tenant_id
        
        service = UserHouseService(db)
        result = service.create_user_house(
            user_house_data=user_house_data,
            current_user=current_user
        )
        
        logger.info(
            "Associazione utente-casa creata",
            extra={
                "user_id": current_user.id,
                "target_user_id": user_house_data.user_id,
                "house_id": user_house_data.house_id,
                "tenant_id": tenant_id
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante la creazione associazione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.get("/{user_id}/{house_id}", response_model=UserHouseResponse)
async def get_user_house(
    user_id: int,
    house_id: int,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(require_permission_in_tenant("manage_house_access")),
    db: Session = Depends(get_db)
):
    """
    Recupera una specifica associazione utente-casa.
    Richiede il permesso 'manage_house_access' nel tenant.
    """
    try:
        service = UserHouseService(db)
        
        # Verifica che l'utente corrente abbia accesso
        if user_id != current_user.id and not service._can_manage_house_access(current_user, house_id, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai i permessi per visualizzare questa associazione"
            )
        
        user_houses = service.get_user_houses(
            current_user=current_user,
            tenant_id=tenant_id,
            user_id=user_id,
            house_id=house_id
        )
        
        if not user_houses.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associazione utente-casa non trovata"
            )
        
        logger.info(
            "Associazione utente-casa recuperata",
            extra={
                "user_id": current_user.id,
                "target_user_id": user_id,
                "house_id": house_id,
                "tenant_id": tenant_id
            }
        )
        
        return user_houses.items[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante il recupero associazione utente-casa",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.put("/{user_id}/{house_id}", response_model=UserHouseResponse)
async def update_user_house(
    user_id: int,
    house_id: int,
    update_data: UserHouseUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(require_permission_in_tenant("manage_house_access")),
    db: Session = Depends(get_db)
):
    """
    Aggiorna un'associazione utente-casa.
    Richiede il permesso 'manage_house_access' nel tenant.
    """
    try:
        service = UserHouseService(db)
        result = service.update_user_house(
            user_id=user_id,
            house_id=house_id,
            tenant_id=tenant_id,
            update_data=update_data,
            current_user=current_user
        )
        
        logger.info(
            "Associazione utente-casa aggiornata con successo",
            extra={
                "user_id": current_user.id,
                "target_user_id": user_id,
                "house_id": house_id,
                "tenant_id": tenant_id
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante l'aggiornamento associazione utente-casa",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.delete("/{user_id}/{house_id}")
async def delete_user_house(
    user_id: int,
    house_id: int,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(require_permission_in_tenant("manage_house_access")),
    db: Session = Depends(get_db)
):
    """
    Elimina un'associazione utente-casa.
    Richiede il permesso 'manage_house_access' nel tenant.
    """
    try:
        service = UserHouseService(db)
        result = service.delete_user_house(
            user_id=user_id,
            house_id=house_id,
            tenant_id=tenant_id,
            current_user=current_user
        )
        
        logger.info(
            "Associazione utente-casa eliminata con successo",
            extra={
                "user_id": current_user.id,
                "target_user_id": user_id,
                "house_id": house_id,
                "tenant_id": tenant_id
            }
        )
        
        return {"message": "Associazione utente-casa eliminata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante l'eliminazione associazione utente-casa",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.get("/my-houses/summary", response_model=List[UserHouseSummary])
async def get_my_houses_summary(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recupera il riepilogo delle case dell'utente corrente.
    Non richiede permessi speciali, solo autenticazione.
    """
    try:
        service = UserHouseService(db)
        result = service.get_user_house_summary(
            current_user=current_user,
            tenant_id=tenant_id
        )
        
        logger.info(
            "Riepilogo case utente recuperato",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "total_houses": len(result)
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Errore durante il recupero riepilogo case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.post("/request-access", response_model=HouseAccessResponse)
async def request_house_access(
    access_request: HouseAccessRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Richiede accesso a una casa.
    Non richiede permessi speciali, solo autenticazione.
    """
    try:
        # Per ora, implementiamo una logica semplice
        # In futuro, potrebbe inviare notifiche al proprietario della casa
        
        service = UserHouseService(db)
        
        # Verifica che la casa esista e appartenga al tenant
        from app.models.house import House
        house = db.get(House, access_request.house_id)
        if not house or house.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Casa non trovata o non appartiene al tenant"
            )
        
        # Verifica se l'utente ha già accesso
        if current_user.has_house_access(access_request.house_id, tenant_id):
            return HouseAccessResponse(
                success=True,
                message="Hai già accesso a questa casa",
                user_house=None
            )
        
        # Per ora, restituiamo un messaggio di richiesta inviata
        # In un'implementazione completa, qui si invierebbe una notifica
        logger.info(
            "Richiesta accesso casa inviata",
            extra={
                "user_id": current_user.id,
                "house_id": access_request.house_id,
                "tenant_id": tenant_id,
                "role_requested": access_request.role_in_house
            }
        )
        
        return HouseAccessResponse(
            success=True,
            message="Richiesta di accesso inviata al proprietario della casa",
            user_house=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Errore durante la richiesta accesso casa",
            extra={
                "user_id": current_user.id,
                "tenant_id": tenant_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        ) 