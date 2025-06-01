from passlib.context import CryptContext

# Configurazione del contesto per l'hashing delle password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Genera un hash sicuro della password usando bcrypt.
    
    Args:
        password (str): Password in chiaro da hashare
        
    Returns:
        str: Password hashata
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se una password in chiaro corrisponde all'hash.
    
    Args:
        plain_password (str): Password in chiaro da verificare
        hashed_password (str): Hash della password da confrontare
        
    Returns:
        bool: True se la password corrisponde, False altrimenti
    """
    return pwd_context.verify(plain_password, hashed_password) 