from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from app.models import House, Node
from app.schemas.node_area import NodeAreaCreate, NodeAreaUpdate
from app.core.deps import get_current_user
from app.models.user import User

class NodeAreaService:
    """Servizio per la gestione delle NodeArea (DISABILITATO - MODELLO RIMOSSO)."""
    # Tutte le funzioni relative a NodeArea sono state commentate/rimosse per evitare errori.
    pass 