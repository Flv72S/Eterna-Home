from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService
from app.db.session import get_session

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_create: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Crea un nuovo utente.
    
    Args:
        user_create (UserCreate): Dati per la creazione dell'utente
        session (Session): Sessione del database
        
    Returns:
        UserRead: Utente creato
        
    Raises:
        HTTPException: Se l'email è già registrata (409)
    """
    try:
        return UserService.create_user(session, user_create)
    except HTTPException as e:
        if e.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email già registrata"
            )
        raise e

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Ottiene i dettagli di un utente specifico.
    
    Args:
        user_id (int): ID dell'utente
        session (Session): Sessione del database
        
    Returns:
        UserRead: Dettagli dell'utente
        
    Raises:
        HTTPException: Se l'utente non esiste (404)
    """
    user = UserService.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    return user

@router.get("/", response_model=List[UserRead])
def get_users(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """
    Ottiene la lista degli utenti con paginazione.
    
    Args:
        skip (int): Numero di record da saltare
        limit (int): Numero massimo di record da restituire
        session (Session): Sessione del database
        
    Returns:
        List[UserRead]: Lista degli utenti
    """
    return UserService.get_users(session, skip=skip, limit=limit)

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session)
):
    """
    Aggiorna i dati di un utente esistente.
    
    Args:
        user_id (int): ID dell'utente
        user_update (UserUpdate): Dati da aggiornare
        session (Session): Sessione del database
        
    Returns:
        UserRead: Utente aggiornato
        
    Raises:
        HTTPException: Se l'utente non esiste (404)
    """
    try:
        return UserService.update_user(session, user_id, user_update)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        raise e

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Elimina un utente.
    
    Args:
        user_id (int): ID dell'utente
        session (Session): Sessione del database
        
    Returns:
        None
        
    Raises:
        HTTPException: Se l'utente non esiste (404)
    """
    try:
        UserService.delete_user(session, user_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        raise e 