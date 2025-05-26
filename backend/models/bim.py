from sqlalchemy import Column, Integer
from backend.db.session import Base

class BIM(Base):
    __tablename__ = "bim"
    id = Column(Integer, primary_key=True, index=True) 