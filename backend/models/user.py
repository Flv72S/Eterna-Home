from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from backend.models.house import House
    from backend.models.maintenance import Maintenance
    from backend.models.annotation import Annotation
    from backend.models.bim import BIM

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: int = Field(default=1)
    role: str = Field(default="user")  # user, admin, maintenance_manager
    full_name: str

    # Relazioni
    houses: List["House"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    maintenance_tasks: List["Maintenance"] = Relationship(back_populates="assigned_to")
    annotations: List["Annotation"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    bim_files: List["BIM"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}) 