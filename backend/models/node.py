from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.db.session import Base
import datetime
import enum

class NodeType(str, enum.Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"

class NodeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(NodeType), nullable=False)
    status = Column(Enum(NodeStatus), nullable=False, default=NodeStatus.INACTIVE)
    last_seen = Column(DateTime, nullable=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    location_x = Column(Float, nullable=True)
    location_y = Column(Float, nullable=True)
    location_z = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    house = relationship("House", back_populates="nodes")
    documents = relationship("Document", back_populates="node", cascade="all, delete-orphan")
    audio_logs = relationship("AudioLog", back_populates="node", cascade="all, delete-orphan")
    legacy_documents = relationship("LegacyDocument", back_populates="node", cascade="all, delete-orphan")
    bim_files = relationship("BIM", back_populates="node", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="node", cascade="all, delete-orphan")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="node", cascade="all, delete-orphan") 