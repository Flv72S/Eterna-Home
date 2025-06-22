import pytest
from fastapi import HTTPException
from faker import Faker

from app.services.user import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.utils.security import verify_password

# Inizializzazione Faker per dati di test
fake = Faker()

@pytest.fixture(name="user_create")
def user_create_fixture():
    return UserCreate(
        email=fake.email(),
        password=fake.password(),
        full_name=fake.name(),
        username=fake.user_name(),
        is_active=True,
        is_superuser=False
    )

# Test Create User
def test_create_user_success(db_session, user_create: UserCreate):
    """Test che verifica la creazione corretta di un utente."""
    user = UserService.create_user(db_session, user_create)
    
    assert user.email == user_create.email
    assert user.is_active == user_create.is_active
    assert user.is_superuser == user_create.is_superuser
    assert user.hashed_password != user_create.password
    assert verify_password(user_create.password, user.hashed_password)

def test_create_user_duplicate_email_raises_error(db_session, user_create: UserCreate):
    """Test che verifica il fallimento della creazione con email duplicata."""
    # Crea il primo utente
    UserService.create_user(db_session, user_create)
    
    # Tenta di creare un secondo utente con la stessa email
    with pytest.raises(HTTPException) as exc_info:
        UserService.create_user(db_session, user_create)
    
    assert exc_info.value.status_code == 400
    assert "Email già registrata" in str(exc_info.value.detail)

def test_create_user_hashes_password(db_session, user_create: UserCreate):
    """Test che verifica l'hashing corretto della password."""
    user = UserService.create_user(db_session, user_create)
    
    assert user.hashed_password != user_create.password
    assert verify_password(user_create.password, user.hashed_password)

# Test Get User
def test_get_user_by_id_success(db_session, user_create: UserCreate):
    """Test che verifica il recupero corretto di un utente tramite ID."""
    created_user = UserService.create_user(db_session, user_create)
    retrieved_user = UserService.get_user(db_session, created_user.id)
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == user_create.email

def test_get_user_by_id_not_found(db_session):
    """Test che verifica il comportamento quando l'ID non esiste."""
    non_existent_id = 999
    user = UserService.get_user(db_session, non_existent_id)
    
    assert user is None

# Test Get User by Email
def test_get_user_by_email_success(db_session, user_create: UserCreate):
    """Test che verifica il recupero corretto di un utente tramite email."""
    created_user = UserService.create_user(db_session, user_create)
    retrieved_user = UserService.get_user_by_email(db_session, user_create.email)
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == user_create.email

def test_get_user_by_email_not_found(db_session):
    """Test che verifica il comportamento quando l'email non esiste."""
    non_existent_email = fake.email()
    user = UserService.get_user_by_email(db_session, non_existent_email)
    
    assert user is None

# Test Update User
def test_update_user_success(db_session, user_create: UserCreate):
    """Test che verifica l'aggiornamento corretto dei dati utente."""
    created_user = UserService.create_user(db_session, user_create)
    
    update_data = UserUpdate(
        email=fake.email(),
        is_active=False
    )
    
    updated_user = UserService.update_user(db_session, created_user.id, update_data)
    
    assert updated_user.email == update_data.email
    assert updated_user.is_active == update_data.is_active
    assert updated_user.id == created_user.id

def test_update_user_password_is_hashed(db_session, user_create: UserCreate):
    """Test che verifica l'hashing della password durante l'aggiornamento."""
    created_user = UserService.create_user(db_session, user_create)
    new_password = fake.password()
    
    update_data = UserUpdate(password=new_password)
    updated_user = UserService.update_user(db_session, created_user.id, update_data)
    
    assert updated_user.hashed_password != new_password
    assert verify_password(new_password, updated_user.hashed_password)

def test_update_user_not_found(db_session):
    """Test che verifica il comportamento quando si tenta di aggiornare un utente non esistente."""
    non_existent_id = 999
    update_data = UserUpdate(email=fake.email())
    
    with pytest.raises(HTTPException) as exc_info:
        UserService.update_user(db_session, non_existent_id, update_data)
    
    assert exc_info.value.status_code == 404
    assert "Utente non trovato" in str(exc_info.value.detail)

# Test Delete User
def test_delete_user_success(db_session, user_create: UserCreate):
    """Test che verifica l'eliminazione corretta di un utente."""
    created_user = UserService.create_user(db_session, user_create)
    
    result = UserService.delete_user(db_session, created_user.id)
    assert result is True
    
    # Verifica che l'utente sia stato effettivamente eliminato
    deleted_user = UserService.get_user(db_session, created_user.id)
    assert deleted_user is None

def test_delete_user_not_found(db_session):
    """Test che verifica il comportamento quando si tenta di eliminare un utente non esistente."""
    non_existent_id = 999
    
    with pytest.raises(HTTPException) as exc_info:
        UserService.delete_user(db_session, non_existent_id)
    
    assert exc_info.value.status_code == 404
    assert "Utente non trovato" in str(exc_info.value.detail)

# Test di integrazione sessione DB
def test_db_session_closes_on_error(db_session):
    """Test che verifica la sessione DB dopo un'operazione con ID non valido."""
    # Esegue un'operazione con ID non valido (stringa)
    result = UserService.get_user(db_session, "invalid_id")
    assert result is None

    # Print temporanei per mostrare lo stato della sessione
    print(f"Session is active: {db_session.is_active}")
    print(f"Session dirty: {db_session.dirty}")
    # La sessione deve essere ancora attiva e non dirty
    assert db_session.is_active
    assert not db_session.dirty

    # Verifica che si possa eseguire una nuova operazione
    user_create = UserCreate(
        email=fake.email(),
        password=fake.password(),
        full_name=fake.name(),
        username=fake.user_name(),
        is_active=True,
        is_superuser=False
    )
    user = UserService.create_user(db_session, user_create)
    assert user is not None 