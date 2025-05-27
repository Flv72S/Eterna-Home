from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.session import Base

class Maintenance(Base):
    __tablename__ = "maintenance"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default='pending')  # pending, in_progress, completed, cancelled
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    cost = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    assigned_to = relationship("User", back_populates="maintenance_tasks") 