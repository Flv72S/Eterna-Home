from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import ConfigDict
from datetime import datetime

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    model_config = ConfigDict(extra="allow")