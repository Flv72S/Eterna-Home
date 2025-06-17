from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.utils.security import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRead, UserResponse
from app.core.security import get_password_hash
from app.core.deps import get_session
from app.db.utils import safe_exec

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    session: Session = Depends(get_session)
) -> UserResponse:
    """Crea un nuovo utente."""
    # Verifica se esiste già un utente con la stessa email
    query = select(User).where(User.email == user.email)
    result = safe_exec(session, query)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email già registrata"
        )
    
    # Verifica se esiste già un utente con lo stesso username
    query = select(User).where(User.username == user.username)
    result = safe_exec(session, query)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username già in uso"
        )
    
    # Crea il nuovo utente
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True,
        is_superuser=False
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return UserResponse.model_validate(db_user)

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Ottiene la lista degli utenti."""
    query = select(User).offset(skip).limit(limit)
    result = safe_exec(session, query)
    users = result.all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Ottieni un utente specifico."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session)
):
    """Aggiorna un utente."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    # Verifica se l'email esiste già (se viene aggiornata)
    if user_data.email and user_data.email != user.email:
        query = select(User).where(User.email == user_data.email)
        result = safe_exec(session, query)
        existing_user = result.first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email già registrata"
            )
    
    # Aggiorna i campi
    user_data_dict = user_data.model_dump(exclude_unset=True)
    for key, value in user_data_dict.items():
        if key == "password" and value is not None:
            user.hashed_password = get_password_hash(value)
        else:
            setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Elimina un utente."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )
    
    try:
        # Elimina prima i documenti associati
        for document in user.documents:
            session.delete(document)
        
        # Elimina le versioni dei documenti
        for doc_version in user.document_versions:
            session.delete(doc_version)
        
        # Elimina le prenotazioni
        for booking in user.bookings:
            session.delete(booking)
        
        # Elimina le case
        for house in user.houses:
            session.delete(house)
        
        # Infine elimina l'utente
        session.delete(user)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'eliminazione dell'utente: {str(e)}"
        )
    
    return None

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user 