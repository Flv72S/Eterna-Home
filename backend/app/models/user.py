from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from pydantic import ConfigDict
from datetime import datetime
from .user_role import UserRole
if TYPE_CHECKING:
    from .role import Role

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    username: Optional[str] = Field(default=None, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRole)

    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)

    def get_permissions(self) -> List[str]:
        perms = set()
        for role in self.roles:
            if role.permissions:
                perms.update(role.permissions)
        return list(perms)

    model_config = ConfigDict(extra="allow")