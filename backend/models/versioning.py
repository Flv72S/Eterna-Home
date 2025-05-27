from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(String(50), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    file_id = Column(Integer, ForeignKey("files.id"))
    
    # Relazioni
    file = relationship("File", back_populates="versions") 