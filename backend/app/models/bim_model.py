from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class BIMModel(SQLModel, table=True):
    __tablename__ = "bim_models"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    file_path: str = Field(max_length=500)
    file_size: int = Field(ge=0)
    file_type: str = Field(max_length=50)
    version: str = Field(max_length=50, default="1.0")
    status: str = Field(max_length=50, default="pending")
    conversion_status: Optional[str] = Field(default=None, max_length=50)
    bim_metadata: Optional[str] = Field(default=None)  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="users.id")
    house_id: int = Field(foreign_key="houses.id")
