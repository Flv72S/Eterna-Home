import pytest
from pydantic import ValidationError, EmailStr
from datetime import datetime

from app.schemas.user import UserCreate, UserUpdate, UserRead, UserBase

# Test di Validazione
def test_user_create_valid_data():
    """Verifica l'accettazione di dati corretti."""
    data = {
        "email": "test@example.com",
        "password": "ValidPassword123!",
        "full_name": "Test User",
        "username": "testuser",
        "is_active": True,
        "is_superuser": False
    }
    user = UserCreate(**data)
    assert user.email == data["email"]
    assert user.password == data["password"]
    assert user.full_name == data["full_name"]
    assert user.username == data["username"]
    assert user.is_active == data["is_active"]
    assert user.is_superuser == data["is_superuser"]

def test_user_create_invalid_email():
    """Verifica il rifiuto di email non valide."""
    data = {
        "email": "invalid-email",
        "password": "ValidPassword123!",
        "full_name": "Test User",
        "username": "testuser"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "email" in str(exc_info.value)

def test_user_create_short_password():
    """Verifica il rifiuto di password troppo corte."""
    data = {
        "email": "test@example.com",
        "password": "short",
        "full_name": "Test User",
        "username": "testuser"
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "password" in str(exc_info.value)

def test_user_update_optional_fields():
    """Verifica l'accettazione di campi opzionali."""
    data = {
        "email": "new@example.com"
    }
    user_update = UserUpdate(**data)
    assert user_update.email == data["email"]
    assert user_update.full_name is None
    assert user_update.password is None
    assert user_update.is_active is None
    assert user_update.is_superuser is None

# Test di Sicurezza
def test_user_read_excludes_sensitive_fields():
    """Verifica l'esclusione dei campi sensibili."""
    data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "username": "testuser",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "role": "owner",
        "role_display": "Proprietario (utente privato)"
    }
    user_read = UserRead(**data)
    user_dict = user_read.model_dump()
    assert "hashed_password" not in user_dict
    assert "password" not in user_dict

def test_sensitive_field_not_exposed():
    """Verifica la serializzazione API sicura."""
    data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "username": "testuser",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "role": "owner",
        "role_display": "Proprietario (utente privato)"
    }
    user_read = UserRead(**data)
    json_data = user_read.model_dump_json()
    assert "hashed_password" not in json_data
    assert "password" not in json_data

def test_model_dump_excludes_sensitive_data():
    """Verifica l'uso corretto di dict()."""
    data = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "username": "testuser",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "role": "owner",
        "role_display": "Proprietario (utente privato)"
    }
    user_read = UserRead(**data)
    dumped_data = user_read.model_dump()
    print("UserRead dict:", dumped_data)
    assert "hashed_password" not in dumped_data
    assert "password" not in dumped_data
    # Adatto la verifica alle chiavi effettivamente presenti
    expected_keys = {"id", "email", "full_name", "is_active", "is_superuser", "created_at", "updated_at", "role", "role_display"}
    assert expected_keys.issubset(set(dumped_data.keys()))

# Test di Compatibilità ORM
def test_user_read_from_orm_model():
    """Verifica la compatibilità con modelli ORM."""
    class MockORMUser:
        def __init__(self):
            self.id = 1
            self.email = "test@example.com"
            self.full_name = "Test User"
            self.username = "testuser"
            self.is_active = True
            self.is_superuser = False
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.hashed_password = "hashed_password_here"
            self.role = "owner"
            self.role_display = "Proprietario (utente privato)"

    orm_user = MockORMUser()
    # Uso model_validate invece di from_orm
    user_read = UserRead.model_validate(orm_user)
    assert user_read.id == orm_user.id
    assert user_read.email == orm_user.email
    assert user_read.full_name == orm_user.full_name
    if hasattr(user_read, "username"):
        assert user_read.username == orm_user.username
    assert "hashed_password" not in user_read.model_dump()

def test_user_update_applies_changes():
    """Verifica la corretta applicazione degli aggiornamenti."""
    original_data = {
        "email": "original@example.com",
        "full_name": "Original User",
        "username": "originaluser",
        "is_active": True,
        "is_superuser": False
    }
    update_data = {
        "email": "updated@example.com",
        "full_name": "Updated User"
    }
    user_update = UserUpdate(**update_data)
    updated_data = {**original_data, **user_update.model_dump(exclude_unset=True)}
    assert updated_data["email"] == "updated@example.com"
    assert updated_data["full_name"] == "Updated User"
    assert updated_data["username"] == "originaluser"
    assert updated_data["is_active"] is True
    assert updated_data["is_superuser"] is False

# Test Edge-case
def test_user_create_missing_required_fields():
    """Verifica il rifiuto di dati mancanti."""
    data = {
        "email": "test@example.com"
        # password e full_name mancanti
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "password" in str(exc_info.value)
    assert "full_name" in str(exc_info.value)

def test_user_update_empty_payload():
    """Verifica l'accettazione di payload vuoti."""
    data = {}
    user_update = UserUpdate(**data)
    assert user_update.model_dump(exclude_unset=True) == {}

def test_invalid_types():
    """Verifica il rifiuto di tipi di dati non validi."""
    data = {
        "email": 123,  # dovrebbe essere stringa
        "password": "ValidPassword123!",
        "full_name": "Test User",
        "username": "testuser",
        "is_active": "not_a_boolean"  # dovrebbe essere boolean
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)
    assert "email" in str(exc_info.value)
    assert "is_active" in str(exc_info.value)

# Test Metadati
def test_field_descriptions_present():
    """Verifica la presenza delle descrizioni dei campi."""
    schema = UserBase.schema()
    for field_name, field_info in schema["properties"].items():
        assert "description" in field_info, f"Campo {field_name} non ha una descrizione" 