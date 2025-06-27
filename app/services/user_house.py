from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlmodel import Session, select, and_, or_
from fastapi import HTTPException, status

from app.models.user_house import UserHouse
from app.models.user import User
from app.models.house import House
from app.schemas.user_house import (
    UserHouseCreate, 
    UserHouseUpdate, 
    UserHouseResponse,
    UserHouseList,
    HouseAccessRequest,
    HouseAccessResponse,
    UserHouseSummary
)
from app.core.logging_multi_tenant import get_logger

logger = get_logger(__name__)

class UserHouseService:
    """Servizio per la gestione delle associazioni utente-casa."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user_house(self, user_house_data: UserHouseCreate, current_user: User) -> UserHouseResponse:
        """Crea una nuova associazione utente-casa."""
        try:
            # Verifica che l'utente corrente abbia i permessi
            if not self._can_manage_house_access(current_user, user_house_data.house_id, user_house_data.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non hai i permessi per gestire l'accesso a questa casa"
                )
            
            # Verifica che la casa esista e appartenga al tenant
            house = self.db.get(House, user_house_data.house_id)
            if not house or house.tenant_id != user_house_data.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Casa non trovata o non appartiene al tenant"
                )
            
            # Verifica che l'utente esista e appartenga al tenant
            user = self.db.get(User, user_house_data.user_id)
            if not user or user.tenant_id != user_house_data.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utente non trovato o non appartiene al tenant"
                )
            
            # Verifica che l'associazione non esista già
            existing = self.db.exec(
                select(UserHouse).where(
                    and_(
                        UserHouse.user_id == user_house_data.user_id,
                        UserHouse.house_id == user_house_data.house_id,
                        UserHouse.tenant_id == user_house_data.tenant_id
                    )
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="L'associazione utente-casa esiste già"
                )
            
            # Crea la nuova associazione
            user_house = UserHouse(
                user_id=user_house_data.user_id,
                house_id=user_house_data.house_id,
                tenant_id=user_house_data.tenant_id,
                role_in_house=user_house_data.role_in_house,
                permissions=user_house_data.permissions,
                is_active=user_house_data.is_active
            )
            
            self.db.add(user_house)
            self.db.commit()
            self.db.refresh(user_house)
            
            logger.info(
                "Associazione utente-casa creata",
                extra={
                    "user_id": current_user.id,
                    "target_user_id": user_house_data.user_id,
                    "house_id": user_house_data.house_id,
                    "tenant_id": user_house_data.tenant_id
                }
            )
            
            return UserHouseResponse.from_orm(user_house)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore durante la creazione associazione utente-casa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def get_user_houses(
        self, 
        current_user: User, 
        tenant_id: uuid.UUID,
        user_id: Optional[int] = None,
        house_id: Optional[int] = None,
        page: int = 1,
        size: int = 50
    ) -> UserHouseList:
        """Recupera le associazioni utente-casa con filtri e paginazione."""
        try:
            # Costruisci la query base
            query = select(UserHouse).where(UserHouse.tenant_id == tenant_id)
            
            # Applica filtri aggiuntivi
            if user_id:
                query = query.where(UserHouse.user_id == user_id)
            if house_id:
                query = query.where(UserHouse.house_id == house_id)
            
            # Verifica che l'utente corrente abbia accesso ai dati richiesti
            if user_id and user_id != current_user.id:
                if not self._can_manage_house_access(current_user, house_id, tenant_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Non hai i permessi per visualizzare queste associazioni"
                    )
            
            # Conta il totale
            total_query = select(UserHouse).where(query.whereclause)
            total = len(self.db.exec(total_query).all())
            
            # Applica paginazione
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            # Esegui la query
            user_houses = self.db.exec(query).all()
            
            # Converti in response
            items = [UserHouseResponse.from_orm(uh) for uh in user_houses]
            
            pages = (total + size - 1) // size
            
            logger.info(
                "Associazioni utente-casa recuperate",
                extra={
                    "user_id": current_user.id,
                    "tenant_id": tenant_id,
                    "total": total,
                    "page": page,
                    "size": size
                }
            )
            
            return UserHouseList(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore durante il recupero associazioni utente-casa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def update_user_house(
        self, 
        user_id: int, 
        house_id: int, 
        tenant_id: uuid.UUID,
        update_data: UserHouseUpdate,
        current_user: User
    ) -> UserHouseResponse:
        """Aggiorna un'associazione utente-casa."""
        try:
            # Verifica che l'utente corrente abbia i permessi
            if not self._can_manage_house_access(current_user, house_id, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non hai i permessi per modificare questa associazione"
                )
            
            # Trova l'associazione
            user_house = self.db.exec(
                select(UserHouse).where(
                    and_(
                        UserHouse.user_id == user_id,
                        UserHouse.house_id == house_id,
                        UserHouse.tenant_id == tenant_id
                    )
                )
            ).first()
            
            if not user_house:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associazione utente-casa non trovata"
                )
            
            # Aggiorna i campi
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(user_house, field, value)
            
            user_house.updated_at = datetime.now(timezone.utc)
            
            self.db.add(user_house)
            self.db.commit()
            self.db.refresh(user_house)
            
            logger.info(
                "Associazione utente-casa aggiornata",
                extra={
                    "user_id": current_user.id,
                    "target_user_id": user_id,
                    "house_id": house_id,
                    "tenant_id": tenant_id
                }
            )
            
            return UserHouseResponse.from_orm(user_house)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento associazione utente-casa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def delete_user_house(
        self, 
        user_id: int, 
        house_id: int, 
        tenant_id: uuid.UUID,
        current_user: User
    ) -> bool:
        """Elimina un'associazione utente-casa."""
        try:
            # Verifica che l'utente corrente abbia i permessi
            if not self._can_manage_house_access(current_user, house_id, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Non hai i permessi per eliminare questa associazione"
                )
            
            # Trova l'associazione
            user_house = self.db.exec(
                select(UserHouse).where(
                    and_(
                        UserHouse.user_id == user_id,
                        UserHouse.house_id == house_id,
                        UserHouse.tenant_id == tenant_id
                    )
                )
            ).first()
            
            if not user_house:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associazione utente-casa non trovata"
                )
            
            # Elimina l'associazione
            self.db.delete(user_house)
            self.db.commit()
            
            logger.info(
                "Associazione utente-casa eliminata",
                extra={
                    "user_id": current_user.id,
                    "target_user_id": user_id,
                    "house_id": house_id,
                    "tenant_id": tenant_id
                }
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Errore durante l'eliminazione associazione utente-casa: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def get_user_house_summary(
        self, 
        current_user: User, 
        tenant_id: uuid.UUID
    ) -> List[UserHouseSummary]:
        """Recupera il riepilogo delle case di un utente."""
        try:
            # Recupera le case di cui è proprietario
            owned_houses = self.db.exec(
                select(House).where(
                    and_(
                        House.owner_id == current_user.id,
                        House.tenant_id == tenant_id
                    )
                )
            ).all()
            
            # Recupera le case associate tramite UserHouse
            user_houses = self.db.exec(
                select(UserHouse).where(
                    and_(
                        UserHouse.user_id == current_user.id,
                        UserHouse.tenant_id == tenant_id,
                        UserHouse.is_active == True
                    )
                )
            ).all()
            
            # Costruisci il riepilogo
            summary = []
            
            # Aggiungi case di proprietà
            for house in owned_houses:
                summary.append(UserHouseSummary(
                    house_id=house.id,
                    house_name=house.name,
                    house_address=house.address,
                    role_in_house="owner",
                    is_owner=True,
                    is_active=True,
                    created_at=house.created_at
                ))
            
            # Aggiungi case associate
            for user_house in user_houses:
                house = self.db.get(House, user_house.house_id)
                if house and house.tenant_id == tenant_id:
                    summary.append(UserHouseSummary(
                        house_id=house.id,
                        house_name=house.name,
                        house_address=house.address,
                        role_in_house=user_house.role_in_house,
                        is_owner=False,
                        is_active=user_house.is_active,
                        created_at=user_house.created_at
                    ))
            
            logger.info(
                "Riepilogo case utente recuperato",
                extra={
                    "user_id": current_user.id,
                    "tenant_id": tenant_id,
                    "total_houses": len(summary)
                }
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Errore durante il recupero riepilogo case utente: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore interno del server"
            )
    
    def _can_manage_house_access(self, user: User, house_id: int, tenant_id: uuid.UUID) -> bool:
        """Verifica se l'utente può gestire l'accesso a una casa."""
        if user.is_superuser:
            return True
        
        if user.tenant_id != tenant_id:
            return False
        
        house = self.db.get(House, house_id)
        if house and house.owner_id == user.id:
            return True
        
        if user.has_role_in_tenant("admin", tenant_id):
            return True
        
        return False 