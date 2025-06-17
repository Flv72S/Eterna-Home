from sqlmodel import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password

class UserService:
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