import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError, EmailStr
from .user import UserBase, UserCreate, UserUpdate, UserRead

def test_user_base_validation():
    """Test UserBase validation."""
    # Valid data
    valid_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }
    user = UserBase(**valid_data)
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_superuser is False

    # Invalid email
    with pytest.raises(ValidationError):
        UserBase(email="invalid-email", full_name="Test User")

    # Invalid full_name (empty)
    with pytest.raises(ValidationError):
        UserBase(email="test@example.com", full_name="")

def test_user_create_valid_data():
    """Verifica che UserCreate accetti dati corretti."""
    valid_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepass123",
        "is_active": True,
        "is_superuser": False
    }
    user = UserCreate(**valid_data)
    assert user.email == valid_data["email"]
    assert user.full_name == valid_data["full_name"]
    assert user.password == valid_data["password"]
    assert user.is_active == valid_data["is_active"]
    assert user.is_superuser == valid_data["is_superuser"]

def test_user_create_invalid_email():
    """Verifica che UserCreate rifiuti email non valide."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="invalid-email",
            full_name="Test User",
            password="securepass123"
        )
    assert "email" in str(exc_info.value)

def test_user_create_short_password():
    """Verifica che UserCreate rifiuti password troppo corte."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="short"
        )
    assert "password" in str(exc_info.value)

def test_user_update_validation():
    """Test UserUpdate validation."""
    # Valid partial update
    valid_data = {
        "email": "new@example.com",
        "password": "newpass123"
    }
    user = UserUpdate(**valid_data)
    assert user.email == "new@example.com"
    assert user.password == "newpass123"
    assert user.full_name is None

    # Invalid email in partial update
    with pytest.raises(ValidationError):
        UserUpdate(email="invalid-email")

def test_user_update_optional_fields():
    """Verifica che UserUpdate accetti campi opzionali."""
    # Test con alcuni campi
    partial_data = {
        "email": "new@example.com",
        "password": "newpass123"
    }
    user = UserUpdate(**partial_data)
    assert user.email == partial_data["email"]
    assert user.password == partial_data["password"]
    assert user.full_name is None
    assert user.is_active is None
    assert user.is_superuser is None

    # Test con tutti i campi None
    empty_data = {
        "email": None,
        "full_name": None,
        "password": None,
        "is_active": None,
        "is_superuser": None
    }
    user = UserUpdate(**empty_data)
    assert all(getattr(user, field) is None for field in empty_data)

def test_user_read_security():
    """Test UserRead security and serialization."""
    # Create a user with sensitive data
    user_data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "hashed_password": "secret_hash",
        "password": "plaintext"
    }
    
    # Create UserRead instance
    user = UserRead(**user_data)
    
    # Convert to dict and verify sensitive data is excluded
    user_dict = user.model_dump()
    assert "hashed_password" not in user_dict
    assert "password" not in user_dict
    
    # Verify all required fields are present
    assert "id" in user_dict
    assert "email" in user_dict
    assert "full_name" in user_dict
    assert "created_at" in user_dict
    assert "updated_at" in user_dict

def test_user_read_orm_compatibility():
    """Test UserRead ORM compatibility."""
    # Simulate ORM model with hashed_password
    class MockUserModel:
        def __init__(self):
            self.id = 1
            self.email = "test@example.com"
            self.full_name = "Test User"
            self.is_active = True
            self.is_superuser = False
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.hashed_password = "secret_hash"

    # Create from ORM model
    mock_user = MockUserModel()
    user = UserRead.model_validate(mock_user)
    
    # Verify sensitive data is excluded
    user_dict = user.model_dump()
    assert "hashed_password" not in user_dict
    assert "password" not in user_dict 

def test_user_read_excludes_sensitive_fields():
    """Verifica che UserRead non esponga dati sensibili."""
    user_data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "hashed_password": "secret_hash",
        "password": "plaintext"
    }
    
    user = UserRead(**user_data)
    user_dict = user.model_dump()
    
    assert "hashed_password" not in user_dict
    assert "password" not in user_dict
    assert all(field in user_dict for field in ["id", "email", "full_name", "created_at", "updated_at"])

def test_sensitive_field_not_exposed():
    """Simula serializzazione API e verifica assenza campi sensibili."""
    user_data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "hashed_password": "secret_hash"
    }
    
    user = UserRead(**user_data)
    json_data = user.model_dump_json()
    
    assert "hashed_password" not in json_data
    assert "password" not in json_data

def test_model_dump_excludes_sensitive_data():
    """Verifica l'uso di model_dump con exclude."""
    user_data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "hashed_password": "secret_hash"
    }
    
    user = UserRead(**user_data)
    user_dict = user.model_dump()
    
    assert "hashed_password" not in user_dict
    assert "password" not in user_dict

def test_user_read_from_orm_model():
    """Verifica la compatibilità con modelli ORM."""
    class MockUserModel:
        def __init__(self):
            self.id = 1
            self.email = "test@example.com"
            self.full_name = "Test User"
            self.is_active = True
            self.is_superuser = False
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.hashed_password = "secret_hash"

    mock_user = MockUserModel()
    user = UserRead.model_validate(mock_user)
    
    assert user.id == mock_user.id
    assert user.email == mock_user.email
    assert "hashed_password" not in user.model_dump()

def test_user_update_applies_changes():
    """Verifica la corretta applicazione degli aggiornamenti."""
    original_data = {
        "email": "old@example.com",
        "full_name": "Old Name",
        "is_active": True
    }
    
    update_data = {
        "email": "new@example.com",
        "full_name": "New Name"
    }
    
    user_update = UserUpdate(**update_data)
    updated_data = {**original_data, **user_update.model_dump(exclude_unset=True)}
    
    assert updated_data["email"] == "new@example.com"
    assert updated_data["full_name"] == "New Name"
    assert updated_data["is_active"] is True

def test_user_create_missing_required_fields():
    """Verifica che UserCreate rifiuti dati mancanti."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email="test@example.com"
            # full_name e password mancanti
        )
    assert "full_name" in str(exc_info.value)
    assert "password" in str(exc_info.value)

def test_user_update_empty_payload():
    """Verifica che UserUpdate accetti payload vuoto."""
    empty_data: Dict[str, Any] = {}
    user = UserUpdate(**empty_data)
    assert all(getattr(user, field) is None for field in ["email", "full_name", "password", "is_active", "is_superuser"])

def test_invalid_types():
    """Verifica che vengano rifiutati tipi di dati non validi."""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            email=123,  # email deve essere stringa
            full_name="Test User",
            password="securepass123"
        )
    assert "email" in str(exc_info.value)

def test_field_descriptions_present():
    """Verifica la presenza delle descrizioni dei campi."""
    for field_name, field in UserBase.model_fields.items():
        assert field.description, f"Campo {field_name} non ha una descrizione"
    
    for field_name, field in UserCreate.model_fields.items():
        assert field.description, f"Campo {field_name} non ha una descrizione"
    
    for field_name, field in UserUpdate.model_fields.items():
        assert field.description, f"Campo {field_name} non ha una descrizione"
    
    for field_name, field in UserRead.model_fields.items():
        assert field.description, f"Campo {field_name} non ha una descrizione" 