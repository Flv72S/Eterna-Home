from sqlalchemy import Column, Integer
from backend.db.session import Base

class Maintenance(Base):
    __tablename__ = "maintenance"
    id = Column(Integer, primary_key=True, index=True) 