from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from backend.db.session import Base

class House(Base):
    __tablename__ = "houses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="houses")
    nodes = relationship("Node", back_populates="house", cascade="all, delete-orphan")
    legacy_documents = relationship("LegacyDocument", back_populates="house", cascade="all, delete-orphan")
    bim_files = relationship("BIM", back_populates="house", cascade="all, delete-orphan") 