from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.models.user import User
from app.utils.password import get_password_hash, verify_password

class UserService:
    """Servizio per la gestione delle operazioni CRUD sugli utenti."""
    
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        try:
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
        except IntegrityError as e:
            self.session.rollback()
            if "ix_user_username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username già in uso"
                )
            elif "ix_user_email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email già in uso"
                )
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        # DEBUG: stampa le tabelle viste dalla sessione
        import sqlalchemy
        try:
            insp = sqlalchemy.inspect(self.session.get_bind())
            tables = insp.get_table_names()
            print(f"[USER SERVICE DEBUG] Tables seen by session: {tables}")
        except Exception as e:
            print(f"[USER SERVICE DEBUG] Errore ispezione tabelle: {e}")
        # Query originale
        statement = select(User).where(User.email == email)
        result = self.session.execute(statement)
        user = result.scalar_one_or_none()
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        statement = select(User).where(User.id == user_id)
        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        return self.get_user_by_id(user_id)

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
        
        try:
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            if "ix_user_username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username già in uso"
                )
            elif "ix_user_email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email già in uso"
                )
            raise

    def authenticate_user(self, email: str, password: str):
        """Authenticate a user. Restituisce un dict con user e stato."""
        user = self.get_user_by_email(email)
        if not user:
            return {"user": None, "error": "not_found"}
        if not verify_password(password, user.hashed_password):
            return {"user": None, "error": "wrong_password"}
        if not user.is_active:
            return {"user": user, "error": "disabled"}
        return {"user": user, "error": None}

    def get_all_users(self) -> list[User]:
        """Restituisce tutti gli utenti."""
        statement = select(User)
        result = self.session.execute(statement)
        return list(result.scalars().all())

    def delete_user(self, user_id: int) -> bool:
        """Elimina un utente dal database."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        self.session.delete(user)
        self.session.commit()
        return True

    def get_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Restituisce una lista di utenti con paginazione.
        Args:
            skip (int): Numero di record da saltare
            limit (int): Numero massimo di record da restituire
        Returns:
            list[User]: Lista degli utenti
        """
        statement = select(User).offset(skip).limit(limit)
        result = self.session.execute(statement)
        return list(result.scalars().all())
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Recupera un utente dal database tramite username.
        
        Args:
            username (str): Username dell'utente da recuperare
            
        Returns:
            Optional[User]: Utente trovato o None
        """
        statement = select(User).where(User.username == username)
        result = self.session.execute(statement)
        user = result.scalar_one_or_none()
        if user:
            # Assicurati che tutti i campi necessari siano presenti
            if not user.full_name:
                user.full_name = user.username
        return user 