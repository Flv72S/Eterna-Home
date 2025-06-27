from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Token(BaseModel):
    """Schema per il token di accesso."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Type of token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Optional[Dict[str, Any]] = Field(default=None, description="User information")

class TokenRefresh(BaseModel):
    """Schema per la richiesta di refresh token."""
    refresh_token: str = Field(..., description="JWT refresh token")

class TokenPayload(BaseModel):
    """Schema per il payload del token."""
    sub: str | None = Field(default=None, description="Subject (user ID)")
    exp: datetime | None = Field(default=None, description="Expiration time")
    type: str | None = Field(default=None, description="Token type (access/refresh)")
    tenant_id: str | None = Field(default=None, description="Tenant ID")
    roles: list[str] | None = Field(default=None, description="User roles")

class TokenRevoke(BaseModel):
    """Schema per la revoca del token."""
    token: str = Field(..., description="Token to revoke")
    reason: Optional[str] = Field(default=None, description="Reason for revocation") 