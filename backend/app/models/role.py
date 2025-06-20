from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from .user_role import UserRole
if TYPE_CHECKING:
    from .user import User

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    permissions: Optional[List[str]] = Field(default_factory=list, sa_column_kwargs={"type_": "JSONB"})

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)

# Import alla fine per evitare import circolari 