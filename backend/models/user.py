from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.db.session import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    role = Column(String(50), default="user")  # user, admin, maintenance_manager
    full_name = Column(String(255), nullable=False)

    houses = relationship("House", back_populates="owner", cascade="all, delete-orphan")
    maintenance_tasks = relationship("Maintenance", back_populates="assigned_to")
    annotations = relationship("Annotation", back_populates="user", cascade="all, delete-orphan") 