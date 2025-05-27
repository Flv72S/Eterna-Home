from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.db.session import Base
import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=True)
    file_path = Column(String(255), nullable=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    node = relationship("Node", back_populates="documents") 