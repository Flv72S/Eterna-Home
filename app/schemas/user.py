from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, ValidationError
from app.models.enums import UserRole
import re

class UserBase(BaseModel):
    """Base schema for user data with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    role: str = Field(
        default=UserRole.get_default_role(),
        description="Ruolo principale dell'utente"
    )

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Valida che il ruolo sia uno di quelli definiti nell'enum."""
        valid_roles = [role.value for role in UserRole]
        if v not in valid_roles:
            raise ValueError(f'Ruolo non valido. Ruoli validi: {", ".join(valid_roles)}')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        extra='allow'  # Permette campi extra nel modello
    )

class UserCreate(UserBase):
    """Schema for creating a new user."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    password: str = Field(..., min_length=8, description="User's password")
    is_active: bool = Field(True, description="Whether the user account is active")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    role: str = Field(
        default=UserRole.get_default_role(),
        description="Ruolo principale dell'utente"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Lunghezza minima già gestita da min_length
        if len(v) > 100:
            raise ValueError('Password must be at most 100 characters long')
        if v.strip() == '' or v.isspace():
            raise ValueError('Password cannot be empty or only spaces')
        if re.search(r'\s', v):
            raise ValueError('Password cannot contain whitespace characters')
        if '\x00' in v:
            raise ValueError('Password cannot contain null bytes')
        # Richiedi almeno una lettera maiuscola, una minuscola, un numero e un simbolo
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        # Escludi alcune password comuni
        common = [
            'password', '123456', '12345678', 'qwerty', 'abc123', 'password1',
            'admin', 'letmein', 'welcome', 'monkey', 'login', 'passw0rd', 'starwars'
        ]
        if v.lower() in common or v.lower().replace(' ', '') in common:
            raise ValueError('Password is too common')
        return v

class UserUpdate(UserBase):
    """Schema for updating user data - all fields optional."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        str_strip_whitespace=True
    )
    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="User's username")
    password: Optional[str] = Field(None, min_length=8, description="User's new password (will be hashed)")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")
    is_superuser: Optional[bool] = Field(None, description="Whether the user has superuser privileges")
    phone_number: Optional[str] = Field(None, description="User's new phone number")
    role: Optional[str] = Field(None, description="Ruolo principale dell'utente")

class UserInDBBase(UserBase):
    id: int = Field(..., description="User's unique identifier")
    is_verified: bool = Field(False, description="Whether the user has been verified")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")
    last_login: Optional[datetime] = Field(None, description="When the user last logged in")

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

class UserRead(UserBase):
    """Schema for reading user data - excludes sensitive information."""
    id: int = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")
    username: str = Field(..., description="User's username")
    role: str = Field(..., description="Ruolo principale dell'utente")
    role_display: str = Field(..., description="Nome visualizzato del ruolo")
    
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
                "username": "johndoe",
                "is_active": True,
                "is_superuser": False,
                "role": "owner",
                "role_display": "Proprietario (utente privato)",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

class UserResponse(BaseModel):
    """Schema per la risposta dell'endpoint /me."""
    id: int = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_superuser: bool = Field(default=False, description="Whether the user has superuser privileges")
    role: str = Field(..., description="Ruolo principale dell'utente")
    role_display: str = Field(..., description="Nome visualizzato del ruolo")
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
                "role": "owner",
                "role_display": "Proprietario (utente privato)",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    ) 