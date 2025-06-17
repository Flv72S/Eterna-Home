from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.models.user import User
from app.utils.password import get_password_hash, verify_password

class UserService:
    """Servizio per la gestione delle operazioni CRUD sugli utenti."""
    
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user_create.password)
        username = user_create.username or user_create.email.split('@')[0]
        db_user = User(
            email=user_create.email,
            username=username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=True
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return self.session.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.session.query(User).filter(User.id == user_id).first()

    def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.session.query(User).filter(User.id == user_id).first()

    def update_user(self, user_id: int, user_update: UserUpdate) -> User | None:
        """Update a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash password if it's being updated
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def delete_user(session: Session, user_id: int) -> bool:
        """
        Elimina un utente dal database.
        
        Args:
            session (Session): Sessione del database
            user_id (int): ID dell'utente da eliminare
            
        Returns:
            bool: True se l'utente è stato eliminato, False se non esiste
            
        Raises:
            HTTPException: Se l'utente non esiste
        """
        db_user = UserService.get_user(session, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
            
        session.delete(db_user)
        session.commit()
        return True
    
    @staticmethod
    def get_users(session: Session, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Restituisce una lista di utenti con paginazione.
        Args:
            session (Session): Sessione del database
            skip (int): Numero di record da saltare
            limit (int): Numero massimo di record da restituire
        Returns:
            list[User]: Lista degli utenti
        """
        statement = select(User).offset(skip).limit(limit)
        result = session.execute(statement)
        return list(result.scalars().all())
    
    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[User]:
        """
        Recupera un utente dal database tramite username.
        
        Args:
            session (Session): Sessione del database
            username (str): Username dell'utente da recuperare
            
        Returns:
            Optional[User]: Utente trovato o None
        """
        query = select(User).where(User.username == username)
        result = session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            # Assicurati che tutti i campi necessari siano presenti
            if not user.full_name:
                user.full_name = user.username
        return user 