from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate, RoleRead
from app.utils.security import get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleRead])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Lista tutti i ruoli disponibili.
    Richiede autenticazione.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo i superuser possono visualizzare i ruoli"
        )
    
    statement = select(Role).offset(skip).limit(limit)
    roles = session.exec(statement).all()
    return roles


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Crea un nuovo ruolo.
    Richiede autenticazione e privilegi di superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo i superuser possono creare ruoli"
        )
    
    # Verifica se il ruolo esiste già
    existing_role = session.exec(
        select(Role).where(Role.name == role_data.name)
    ).first()
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo con nome '{role_data.name}' già esistente"
        )
    
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions
    )
    
    session.add(role)
    session.commit()
    session.refresh(role)
    
    return role


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Recupera i dettagli di un ruolo specifico.
    Richiede autenticazione e privilegi di superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo i superuser possono visualizzare i dettagli dei ruoli"
        )
    
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruolo non trovato"
        )
    
    return role


@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Aggiorna un ruolo esistente.
    Richiede autenticazione e privilegi di superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo i superuser possono modificare i ruoli"
        )
    
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruolo non trovato"
        )
    
    # Verifica se il nuovo nome è già utilizzato da un altro ruolo
    if role_data.name and role_data.name != role.name:
        existing_role = session.exec(
            select(Role).where(Role.name == role_data.name)
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ruolo con nome '{role_data.name}' già esistente"
            )
    
    # Aggiorna i campi forniti
    role_data_dict = role_data.model_dump(exclude_unset=True)
    for field, value in role_data_dict.items():
        setattr(role, field, value)
    
    session.add(role)
    session.commit()
    session.refresh(role)
    
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Elimina un ruolo.
    Richiede autenticazione e privilegi di superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo i superuser possono eliminare i ruoli"
        )
    
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruolo non trovato"
        )
    
    # Verifica se il ruolo è assegnato a qualche utente
    from app.models.user_role import UserRole
    user_roles = session.exec(
        select(UserRole).where(UserRole.role_id == role_id)
    ).all()
    
    if user_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare il ruolo: è ancora assegnato ad alcuni utenti"
        )
    
    session.delete(role)
    session.commit()
    
    return None 