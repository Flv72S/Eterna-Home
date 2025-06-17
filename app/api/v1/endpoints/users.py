from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user import UserService
from app.core.security import get_password_hash
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    session: Session = Depends(get_session)
) -> UserResponse:
    """Crea un nuovo utente."""
    print("DEBUG: Entrato in endpoint create_user")
    try:
        return UserService.create_user(session, user)
    except HTTPException as e:
        if e.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email già registrata"
            )
        raise e

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Ottiene un utente specifico."""
    user = UserService.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """Ottiene una lista di utenti con paginazione."""
    return UserService.get_users(session, skip=skip, limit=limit)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Ottiene i dettagli dell'utente corrente."""
    return UserResponse.model_validate(current_user.model_dump())

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session)
):
    """Aggiorna un utente esistente."""
    user = UserService.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    return UserService.update_user(session, user, user_update)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Elimina un utente."""
    user = UserService.get_user(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    UserService.delete_user(session, user)
    return None 