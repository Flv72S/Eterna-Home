from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Base schema for user data with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="User's password (will be hashed)")
    username: str

class UserUpdate(BaseModel):
    """Schema for updating user data - all fields optional."""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    password: Optional[str] = Field(None, min_length=8, description="User's new password (will be hashed)")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")
    is_superuser: Optional[bool] = Field(None, description="Whether the user has superuser privileges")

class UserRead(UserBase):
    """Schema for reading user data - excludes sensitive information."""
    id: int = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")
    full_name: Optional[str] = Field(None, description="Nome completo dell'utente")
    username: str = Field(..., description="User's username")
    
    # Exclude hashed_password from serialization
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

class UserResponse(UserRead):
    """Schema per la risposta dell'endpoint /me."""
    pass 