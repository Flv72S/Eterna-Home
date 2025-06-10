from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from . import random_lower_string

def create_random_user(
    db: Session,
    *,
    email: Optional[str] = None,
    password: Optional[str] = None,
    username: Optional[str] = None,
    is_superuser: bool = False,
) -> User:
    if not email:
        email = f"{random_lower_string()}@example.com"
    if not password:
        password = random_lower_string()
    if not username:
        username = random_lower_string()
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user 