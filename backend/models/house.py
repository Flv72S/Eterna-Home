from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.session import Base

class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="houses")
    nodes = relationship("Node", back_populates="house", cascade="all, delete-orphan")
    legacy_documents = relationship("LegacyDocument", back_populates="house", cascade="all, delete-orphan")
    bim_files = relationship("BIM", back_populates="house", cascade="all, delete-orphan") 