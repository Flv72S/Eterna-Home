from pydantic import BaseModel

class Token(BaseModel):
    """Schema per il token di accesso."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Schema per il payload del token."""
    sub: str | None = None 