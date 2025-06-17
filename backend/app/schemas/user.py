from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from typing import Optional
import re

class UserBase(BaseModel):
    """Base schema for user data with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")
    is_verified: bool = Field(default=False, description="Whether the user's email has been verified")

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        extra='allow'
    )

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password")
    username: Optional[str] = Field(None, description="User's username")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La password deve essere di almeno 8 caratteri')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La password deve contenere almeno una lettera maiuscola')
        if not re.search(r'[a-z]', v):
            raise ValueError('La password deve contenere almeno una lettera minuscola')
        if not re.search(r'\d', v):
            raise ValueError('La password deve contenere almeno un numero')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('La password deve contenere almeno un carattere speciale')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user data."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('La password deve essere di almeno 8 caratteri')
            if not re.search(r'[A-Z]', v):
                raise ValueError('La password deve contenere almeno una lettera maiuscola')
            if not re.search(r'[a-z]', v):
                raise ValueError('La password deve contenere almeno una lettera minuscola')
            if not re.search(r'\d', v):
                raise ValueError('La password deve contenere almeno un numero')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('La password deve contenere almeno un carattere speciale')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        extra='allow'
    )

class UserRead(UserBase):
    id: int
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True, extra="allow")