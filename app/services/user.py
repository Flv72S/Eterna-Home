from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.models.user import User
from app.utils.security import get_password_hash

class UserService:
    """Servizio per la gestione delle operazioni CRUD sugli utenti."""
    
    @staticmethod
    def create_user(session: Session, user_create: UserCreate) -> User:
        """
        Crea un nuovo utente nel database.
        
        Args:
            session (Session): Sessione del database
            user_create (UserCreate): Dati per la creazione dell'utente
            
        Returns:
            User: Utente creato
            
        Raises:
            HTTPException: Se l'email è già in uso
        """
        # Verifica se l'email è già in uso
        if UserService.get_user_by_email(session, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email già registrata"
            )
            
        # Crea il nuovo utente con password hashata
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=get_password_hash(user_create.password),
            is_active=user_create.is_active,
            is_superuser=user_create.is_superuser
        )
        
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user(session: Session, user_id: int) -> Optional[User]:
        """
        Recupera un utente dal database tramite ID.
        
        Args:
            session (Session): Sessione del database
            user_id (int): ID dell'utente da recuperare
            
        Returns:
            Optional[User]: Utente trovato o None
        """
        return session.get(User, user_id)
    
    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """
        Recupera un utente dal database tramite email.
        
        Args:
            session (Session): Sessione del database
            email (str): Email dell'utente da recuperare
            
        Returns:
            Optional[User]: Utente trovato o None
        """
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()
    
    @staticmethod
    def update_user(session: Session, user_id: int, user_update: UserUpdate) -> User:
        """
        Aggiorna i dati di un utente esistente.
        
        Args:
            session (Session): Sessione del database
            user_id (int): ID dell'utente da aggiornare
            user_update (UserUpdate): Dati da aggiornare
            
        Returns:
            User: Utente aggiornato
            
        Raises:
            HTTPException: Se l'utente non esiste
        """
        db_user = UserService.get_user(session, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
            
        # Aggiorna i campi forniti
        user_data = user_update.dict(exclude_unset=True)
        if "password" in user_data:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
            
        for key, value in user_data.items():
            setattr(db_user, key, value)
            
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    
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