from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.db.session import Base
import datetime

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), default="active")
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    house = relationship("House", back_populates="nodes")
    documents = relationship("Document", back_populates="node", cascade="all, delete-orphan")
    audio_logs = relationship("AudioLog", back_populates="node", cascade="all, delete-orphan")
    legacy_documents = relationship("LegacyDocument", back_populates="node", cascade="all, delete-orphan")
    bim_files = relationship("BIM", back_populates="node", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="node", cascade="all, delete-orphan") 