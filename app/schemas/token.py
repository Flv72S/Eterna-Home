from typing import Optional, Dict, Any
from pydantic import BaseModel

class Token(BaseModel):
    """Schema per il token di accesso."""
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None

class TokenPayload(BaseModel):
    """Schema per il payload del token."""
    sub: str | None = None 