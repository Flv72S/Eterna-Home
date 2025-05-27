from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class BIM(Base):
    __tablename__ = "bim_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    house_id = Column(Integer, ForeignKey('houses.id'), nullable=False)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=True)
    bim_file_url = Column(String, nullable=False)
    version = Column(String, nullable=False)
    format = Column(String, nullable=False)  # IFC, RVT, DWG
    size_mb = Column(Float, nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    description = Column(String, nullable=True)
    
    # Relazioni
    user = relationship("User", back_populates="bim_files")
    house = relationship("House", back_populates="bim_files")
    node = relationship("Node", back_populates="bim_files") 