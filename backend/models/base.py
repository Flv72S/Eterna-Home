from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional, TYPE_CHECKING, Any
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .house import House
    from .node import Node
    from .document import Document
    from .audio_log import AudioLog

__all__ = ["Base", "Column", "Integer", "String", "ForeignKey", "DateTime", "func",
           "relationship", "Mapped", "List", "Optional", "datetime"]

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

# Importazioni alla fine per evitare cicli
from .user import User
from .house import House
from .node import Node
from .document import Document
from .audio_log import AudioLog 