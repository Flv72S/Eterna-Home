from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.db.session import Base
import datetime

class AudioLog(Base):
    __tablename__ = "audio_logs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    duration = Column(Integer, nullable=True)  # durata in secondi
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    node = relationship("Node", back_populates="audio_logs") 