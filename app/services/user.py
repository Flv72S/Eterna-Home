from typing import Optional, List
from sqlmodel import Session, select
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.models.user import User
from app.models.enums import UserRole
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
                role=user_create.role,
                is_superuser=user_create.is_superuser,
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
        print(f"DEBUG GET_USER_BY_EMAIL: Starting query for email={email}")
        print(f"DEBUG GET_USER_BY_EMAIL: User model type={type(User)}")
        print(f"DEBUG GET_USER_BY_EMAIL: User.__tablename__={getattr(User, '__tablename__', 'NOT_SET')}")
        
        statement = select(User).where(User.email == email)
        print(f"DEBUG GET_USER_BY_EMAIL: SQL statement={statement}")
        
        result = self.session.execute(statement)
        print(f"DEBUG GET_USER_BY_EMAIL: Query result type={type(result)}")
        
        # Debug: vediamo cosa contiene il risultato
        rows = result.fetchall()
        print(f"DEBUG GET_USER_BY_EMAIL: Number of rows returned: {len(rows)}")
        if rows:
            print(f"DEBUG GET_USER_BY_EMAIL: First row type: {type(rows[0])}")
            print(f"DEBUG GET_USER_BY_EMAIL: First row content: {rows[0]}")
        
        # Reset the result per poter usare scalar_one_or_none
        result = self.session.execute(statement)
        user = result.scalar_one_or_none()
        print(f"DEBUG GET_USER_BY_EMAIL: email={email}, user={user}, user_type={type(user)}")
        if user:
            print(f"DEBUG GET_USER_BY_EMAIL: user.id={user.id}, user.email={user.email}, user.username={user.username}")
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
        
        update_data = user_update.model_dump(exclude_unset=True)
        
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

    def authenticate_user(self, email_or_username: str, password: str):
        """Authenticate a user. Supporta sia email che username. Restituisce un dict con user e stato."""
        print(f"DEBUG AUTHENTICATE_USER: email_or_username={email_or_username}, password={password}")
        # Prova prima con email
        user = self.get_user_by_email(email_or_username)
        print(f"DEBUG AUTHENTICATE_USER: after get_user_by_email, user={user}")
        if user:
            print(f"DEBUG AUTH: user.id={user.id}, email={user.email}, username={user.username}, hashed_password={user.hashed_password}, password_in_test={password}")
            # Verifica la password per l'utente trovato per email
            if not verify_password(password, user.hashed_password):
                return {"user": None, "error": "wrong_password"}
            if not user.is_active:
                return {"user": user, "error": "disabled"}
            return {"user": user, "error": None}
        
        print(f"DEBUG AUTHENTICATE_USER: user not found by email, trying username")
        # Se non trova per email, prova con username
        user = self.get_user_by_username(email_or_username)
        print(f"DEBUG AUTHENTICATE_USER: after get_user_by_username, user={user}")
        if user:
            print(f"DEBUG AUTH: user.id={user.id}, email={user.email}, username={user.username}, hashed_password={user.hashed_password}, password_in_test={password}")
            # Verifica la password per l'utente trovato per username
            if not verify_password(password, user.hashed_password):
                return {"user": None, "error": "wrong_password"}
            if not user.is_active:
                return {"user": user, "error": "disabled"}
            return {"user": user, "error": None}
        
        # Se non trova né per email né per username
        print(f"DEBUG AUTHENTICATE_USER: user not found by email or username")
        return {"user": None, "error": "not_found"}

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
    
    def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Recupera tutti gli utenti con un ruolo specifico.
        
        Args:
            role (UserRole): Ruolo da filtrare
            skip (int): Numero di record da saltare
            limit (int): Numero massimo di record da restituire
            
        Returns:
            List[User]: Lista degli utenti con il ruolo specificato
        """
        statement = select(User).where(User.role == role.value, User.is_active == True).offset(skip).limit(limit)
        result = self.session.execute(statement)
        return list(result.scalars().all())
    
    def count_users_by_role(self, role: UserRole) -> int:
        """
        Conta il numero di utenti con un ruolo specifico.
        
        Args:
            role (UserRole): Ruolo da contare
            
        Returns:
            int: Numero di utenti con il ruolo specificato
        """
        from sqlalchemy import func
        statement = select(func.count(User.id)).where(User.role == role.value, User.is_active == True)
        result = self.session.execute(statement)
        return result.scalar()
    
    def update_user_role(self, user_id: int, new_role: UserRole) -> User:
        """
        Aggiorna il ruolo di un utente.
        
        Args:
            user_id (int): ID dell'utente
            new_role (UserRole): Nuovo ruolo
            
        Returns:
            User: Utente aggiornato
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        user.role = new_role.value
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_user_stats(self) -> dict:
        """
        Restituisce statistiche sugli utenti per ruolo.
        
        Returns:
            dict: Statistiche sugli utenti
        """
        stats = {}
        for role in UserRole:
            count = len(self.get_users_by_role(role))
            stats[role.value] = {
                "count": count,
                "display_name": role.get_display_name(role.value)
            }
        return stats 