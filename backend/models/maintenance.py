from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
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

class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    node_id = Column(Integer, ForeignKey("nodes.id"))
    
    # Relazioni
    node = relationship("Node", back_populates="maintenance_tasks") 