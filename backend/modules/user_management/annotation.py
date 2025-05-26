from sqlalchemy import Column, Integer
from backend.db.session import Base

class Annotation(Base):
    __tablename__ = "annotation"
    id = Column(Integer, primary_key=True, index=True) 