from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserResponse(BaseModel):
    """Schema per la risposta dell'endpoint /me."""
    id: int = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        extra='allow',
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    ) 