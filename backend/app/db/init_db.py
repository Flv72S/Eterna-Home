from sqlmodel import SQLModel, select
from sqlalchemy import text
from app.db.session import engine
from app.models.user import User
from app.core.config import settings

def init_db() -> None:
    """Initialize the database."""
    # Drop all tables
    SQLModel.metadata.drop_all(engine)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    # Create initial superuser
    from app.services.user import UserService
    from app.schemas.user import UserCreate
    
    superuser = UserCreate(
        email=settings.FIRST_SUPERUSER,
        username="admin",
        password=settings.FIRST_SUPERUSER_PASSWORD,
        full_name="Admin User",
        is_superuser=True
    )
    
    with engine.connect() as conn:
        UserService.create_user(conn, superuser)

if __name__ == "__main__":
    init_db() 