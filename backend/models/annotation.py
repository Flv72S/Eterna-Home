from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Annotation(Base):
    __tablename__ = "annotation"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text_content = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    type = Column(String, nullable=False)  # text, image, audio, voice_log
    
    # Relazioni
    node = relationship("Node", back_populates="annotations")
    user = relationship("User", back_populates="annotations") 