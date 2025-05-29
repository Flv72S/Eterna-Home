from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.house import House

class BIM(SQLModel, table=True):
    __tablename__ = "bim_files"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    file_path: str = Field(max_length=255, nullable=False)
    file_type: str = Field(max_length=50, nullable=False)
    version: str = Field(max_length=50, nullable=False)
    house_id: int = Field(foreign_key="houses.id", nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    house: "House" = Relationship(back_populates="bim_files")
    user: "User" = Relationship(back_populates="bim_files") 