from sqlmodel import Session, select
from typing import TypeVar, Type, Optional, List, Any

T = TypeVar('T')

def safe_exec(session: Session, query: Any) -> Any:
    """
    Esegue una query in modo sicuro, gestendo correttamente i parametri.
    
    Args:
        session: La sessione del database
        query: La query da eseguire
        
    Returns:
        Il risultato della query
    """
    try:
        return session.exec(query)
    except TypeError as e:
        if "takes 2 positional arguments but 3 were given" in str(e):
            # Se la query è una select, esegui direttamente
            if isinstance(query, select):
                return session.exec(query)
            # Altrimenti, esegui la query con i parametri
            return session.execute(query)
        raise 