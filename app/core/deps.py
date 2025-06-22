from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional

from app.core.config import settings
from app.db.session import get_session
from app.db.utils import safe_exec
from app.models.user import User
from app.utils.security import get_cached_user, cache_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_db():
    """Get database session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        print(f"[DEBUG] Token payload: {payload}")
        print(f"[DEBUG] Email from token: {email}")
        if email is None:
            print("[DEBUG] Email is None, raising credentials_exception")
            raise credentials_exception
    except JWTError as e:
        print(f"[DEBUG] JWT decode error: {e}")
        raise credentials_exception

    # Try to get user from cache first
    cached_user = get_cached_user(email)
    if cached_user:
        print(f"[DEBUG] User found in cache: {cached_user}")
        return User(**cached_user)

    # If not in cache, get from database
    query = select(User).where(User.email == email)
    result = safe_exec(session, query)
    user = result.first()
    print(f"[DEBUG] User from database: {user}")
    if user is None:
        print(f"[DEBUG] User not found in database for email: {email}")
        raise credentials_exception

    # Cache the user for future requests
    cache_user(user, email)
    
    return user 