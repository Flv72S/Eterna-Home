from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class LegacyDocument(Base):
    __tablename__ = "legacy_documents"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    type = Column(String, nullable=False)  # es. 'PDF', 'JPG'
    file_url = Column(String, nullable=False)
    filename = Column(String, nullable=False)  # Nome originale del file
    version = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relazioni
    house = relationship("House", back_populates="legacy_documents")
    node = relationship("Node", back_populates="legacy_documents") 