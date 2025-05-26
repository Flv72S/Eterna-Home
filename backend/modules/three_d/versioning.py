from sqlalchemy import Column, Integer
from backend.db.session import Base

class Versioning(Base):
    __tablename__ = "versioning"
    id = Column(Integer, primary_key=True, index=True) 