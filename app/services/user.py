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

    @staticmethod
    def create_user(session: Session, user_create: UserCreate) -> User:
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
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return db_user
        except IntegrityError as e:
            session.rollback()
            # Gestione robusta: qualsiasi errore di chiave duplicata su email
            if "email" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email già registrata"
                )
            if "username" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username già in uso"
                )
            raise

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        print(f"DEBUG GET_USER_BY_EMAIL: Starting query for email={email}")
        print(f"DEBUG GET_USER_BY_EMAIL: User model type={type(User)}")
        print(f"DEBUG GET_USER_BY_EMAIL: User.__tablename__={getattr(User, '__tablename__', 'NOT_SET')}")
        
        statement = select(User).where(User.email == email)
        print(f"DEBUG GET_USER_BY_EMAIL: SQL statement={statement}")
        
        result = session.execute(statement)
        print(f"DEBUG GET_USER_BY_EMAIL: Query result type={type(result)}")
        
        # Debug: vediamo cosa contiene il risultato
        rows = result.fetchall()
        print(f"DEBUG GET_USER_BY_EMAIL: Number of rows returned: {len(rows)}")
        if rows:
            print(f"DEBUG GET_USER_BY_EMAIL: First row type: {type(rows[0])}")
            print(f"DEBUG GET_USER_BY_EMAIL: First row content: {rows[0]}")
        
        # Reset the result per poter usare scalar_one_or_none
        result = session.execute(statement)
        user = result.scalar_one_or_none()
        print(f"DEBUG GET_USER_BY_EMAIL: email={email}, user={user}, user_type={type(user)}")
        if user:
            print(f"DEBUG GET_USER_BY_EMAIL: user.id={user.id}, user.email={user.email}, user.username={user.username}")
        return user

    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> User | None:
        """Get a user by ID."""
        # Gestione robusta: se user_id non è int, restituisco None
        try:
            if not isinstance(user_id, int):
                return None
            statement = select(User).where(User.id == user_id)
            result = session.execute(statement)
            return result.scalar_one_or_none()
        except Exception:
            return None

    @staticmethod
    def get_user(session: Session, user_id: int) -> User | None:
        """Get a user by ID."""
        return UserService.get_user_by_id(session, user_id)

    @staticmethod
    def update_user(session: Session, user_id: int, user_update: UserUpdate) -> User | None:
        """Update a user."""
        user = UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        update_data = user_update.model_dump(exclude_unset=True)
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        for field, value in update_data.items():
            setattr(user, field, value)
        try:
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError as e:
            session.rollback()
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

    @staticmethod
    def authenticate_user(session: Session, email_or_username: str, password: str):
        """Authenticate a user. Supporta sia email che username. Restituisce un dict con user e stato."""
        print(f"DEBUG AUTHENTICATE_USER: email_or_username={email_or_username}, password={password}")
        # Prova prima con email
        user = UserService.get_user_by_email(session, email_or_username)
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
        user = UserService.get_user_by_username(session, email_or_username)
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

    @staticmethod
    def get_all_users(session: Session) -> list[User]:
        """Restituisce tutti gli utenti."""
        statement = select(User)
        result = session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    def delete_user(session: Session, user_id: int) -> bool:
        """Elimina un utente dal database."""
        user = UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        session.delete(user)
        session.commit()
        return True

    @staticmethod
    def get_users(session: Session, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Restituisce una lista di utenti con paginazione.
        Args:
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
            username (str): Username dell'utente da recuperare
            
        Returns:
            Optional[User]: Utente trovato o None
        """
        statement = select(User).where(User.username == username)
        result = session.execute(statement)
        user = result.scalar_one_or_none()
        
        if user:
            # Assicurati che tutti i campi necessari siano presenti
            if not user.full_name:
                user.full_name = user.username
        return user
    
    @staticmethod
    def get_users_by_role(session: Session, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
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
        result = session.execute(statement)
        return list(result.scalars().all())
    
    @staticmethod
    def count_users_by_role(session: Session, role: UserRole) -> int:
        """
        Conta il numero di utenti con un ruolo specifico.
        
        Args:
            role (UserRole): Ruolo da contare
            
        Returns:
            int: Numero di utenti con il ruolo specificato
        """
        from sqlalchemy import func
        statement = select(func.count(User.id)).where(User.role == role.value, User.is_active == True)
        result = session.execute(statement)
        return result.scalar()
    
    @staticmethod
    def update_user_role(session: Session, user_id: int, new_role: UserRole) -> User:
        """
        Aggiorna il ruolo di un utente.
        
        Args:
            user_id (int): ID dell'utente
            new_role (UserRole): Nuovo ruolo
            
        Returns:
            User: Utente aggiornato
        """
        user = UserService.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        user.role = new_role.value
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def get_user_stats(session: Session) -> dict:
        """
        Restituisce statistiche sugli utenti per ruolo.
        
        Returns:
            dict: Statistiche sugli utenti
        """
        stats = {}
        for role in UserRole:
            count = len(UserService.get_users_by_role(session, role))
            stats[role.value] = {
                "count": count,
                "display_name": role.get_display_name(role.value)
            }
        return stats 