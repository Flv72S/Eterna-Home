import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel
from sqlalchemy import create_engine
import time
import logging
from faker import Faker
import threading
from contextlib import contextmanager
from sqlalchemy import text

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session
from app.core.security import get_password_hash

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

fake = Faker()

@contextmanager
def timeout(seconds):
    """Timeout context manager che funziona su Windows."""
    timer = threading.Timer(seconds, lambda: (_ for _ in ()).throw(TimeoutError(f"Test timed out after {seconds} seconds")))
    timer.start()
    try:
        yield
    finally:
        timer.cancel()

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user_create = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User",
        username="testuser"
    )
    user_service = UserService(session)
    return user_service.create_user(user_create)

@pytest.fixture
def test_user_data():
    """Genera dati utente unici per il test"""
    return {
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": "Test123!@#",
        "full_name": fake.name()
    }

@pytest.fixture
def existing_user(session: Session):
    user = User(
        email="existing@example.com",
        username="existinguser",
        hashed_password=get_password_hash("Test123!@#"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="auth_token")
def auth_token_fixture(client: TestClient, test_user: User):
    """Fixture per ottenere un token di autenticazione valido."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "TestPassword123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(auth_token: str):
    """Fixture per ottenere gli headers di autenticazione."""
    return {"Authorization": f"Bearer {auth_token}"}

# Test 1.1.1: GET /users/me - Successo
def test_read_users_me(client: TestClient, test_user: User, auth_headers: dict):
    """Verifica che l'endpoint /users/me restituisca i dati dell'utente autenticato."""
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["full_name"] == "Test User"

# Test 1.1.2: GET /users/me - Non autenticato
def test_read_users_me_unauthorized(client: TestClient):
    """Verifica che l'endpoint /users/me restituisca errore 401 se non autenticato."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

# Test 1.1.3: GET /users/me - Token non valido
def test_read_users_me_invalid_token(client: TestClient):
    """Verifica che l'endpoint /users/me restituisca errore 401 con token non valido."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.timeout(30)
def test_create_user_valid_data(client: TestClient, test_user_data):
    """Test creazione utente con dati validi"""
    print("DEBUG: Inizio test_create_user_valid_data")
    start_time = time.time()
    
    try:
        with timeout(30):  # Timeout di 30 secondi
            response = client.post("/api/v1/auth/register", json=test_user_data)
            print(f"DEBUG: Risposta ricevuta dopo {time.time() - start_time:.2f} secondi")
            print(f"DEBUG: Status code: {response.status_code}")
            print(f"DEBUG: Risposta: {response.text}")
            
            assert response.status_code == 201
            data = response.json()
            
            # Verifica campi obbligatori
            assert "id" in data
            assert data["email"] == test_user_data["email"]
            assert data["username"] == test_user_data["username"]
            assert data["full_name"] == test_user_data["full_name"]
            
            # Verifica campi di default
            assert data["is_active"] is True
            assert data["is_superuser"] is False
            
            # Verifica campi di audit
            assert "created_at" in data
            assert "updated_at" in data
            
            # Verifica che i campi sensibili non siano presenti
            assert "password" not in data
            assert "hashed_password" not in data
    except TimeoutError as e:
        print(f"DEBUG: Test timeout dopo {time.time() - start_time:.2f} secondi")
        raise
    except Exception as e:
        print(f"DEBUG: Errore durante il test dopo {time.time() - start_time:.2f} secondi")
        print(f"DEBUG: Errore: {str(e)}")
        raise

def test_create_user_missing_required_fields(client: TestClient):
    """Test creazione utente con campi obbligatori mancanti."""
    # Test senza email
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "Test123!@#"
    })
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert isinstance(errors, list)
    assert any(error["loc"][-1] == "email" for error in errors)
    assert any("field required" in error["msg"].lower() for error in errors)

    # Test senza username
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "Test123!@#"
    })
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert isinstance(errors, list)
    assert any(error["loc"][-1] == "username" for error in errors)
    assert any("field required" in error["msg"].lower() for error in errors)

    # Test senza password
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser"
    })
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert isinstance(errors, list)
    assert any(error["loc"][-1] == "password" for error in errors)
    assert any("field required" in error["msg"].lower() for error in errors)

@pytest.mark.parametrize("invalid_email", [
    "notanemail",           # Email senza @
    "missing@",             # Email senza dominio
    "@nodomain",            # Email senza username
    "spaces in@email.com",  # Email con spazi
    "no.dot@com",           # Email senza punto nel dominio
    "user@.com",            # Email senza dominio prima del punto
    "user@domain.",         # Email senza TLD
    "user@domain..com",     # Email con doppio punto nel dominio
    "user@-domain.com",     # Email con trattino all'inizio del dominio
    "user@domain-.com",     # Email con trattino alla fine del dominio
    "user@domain.com.",     # Email con punto alla fine
    ".user@domain.com",     # Email con punto all'inizio
    "user..name@domain.com" # Email con doppio punto nell'username
])
def test_create_user_invalid_email(client: TestClient, test_user_data, invalid_email):
    """Test creazione utente con email non valida."""
    print(f"DEBUG: Test email non valida: {invalid_email}")
    
    # Modifica l'email nel test_user_data
    test_data = test_user_data.copy()
    test_data["email"] = invalid_email
    
    try:
        with timeout(30):  # Timeout di 30 secondi
            response = client.post("/api/v1/auth/register", json=test_data)
            print(f"DEBUG: Status code: {response.status_code}")
            print(f"DEBUG: Risposta: {response.text}")
            
            # Verifica che la risposta sia 422 (Unprocessable Entity)
            assert response.status_code == 422
            
            # Verifica che la risposta contenga un messaggio di errore appropriato
            error_data = response.json()
            assert "detail" in error_data
            
            # Verifica che l'errore sia relativo all'email
            error_messages = [err["msg"] for err in error_data["detail"]]
            assert any("email" in msg.lower() for msg in error_messages)
            
    except TimeoutError as e:
        print(f"DEBUG: Test timeout dopo {time.time() - start_time:.2f} secondi")
        raise
    except Exception as e:
        print(f"DEBUG: Errore durante il test dopo {time.time() - start_time:.2f} secondi")
        print(f"DEBUG: Errore: {str(e)}")
        raise

@pytest.mark.parametrize("invalid_password", [
    "short",           # Password troppo corta
    "12345678",       # Solo numeri
    "abcdefgh",       # Solo lettere minuscole
    "ABCDEFGH",       # Solo lettere maiuscole
    "!@#$%^&*",       # Solo caratteri speciali
    "password123",    # Password comune
    "qwerty123",      # Sequenza di tasti
    "admin123",       # Password comune con admin
    "letmein123",     # Password comune
    "welcome123",     # Password comune
    " " * 12,         # Solo spazi
    "pass word",      # Con spazi
    "pass\tword",     # Con tab
    "pass\nword",     # Con newline
    "pass\rword",     # Con carriage return
    "pass\x00word",   # Con null byte
    "pass\xffword",   # Con carattere non valido
    "pass\x7fword",   # Con carattere di controllo
    "pass\x1bword",   # Con escape
    "pass\x1aword"    # Con substitute
])
def test_create_user_invalid_password(client: TestClient, test_user_data, invalid_password):
    """Test creazione utente con password non valida."""
    print(f"DEBUG: Test password non valida: {invalid_password}")
    
    # Modifica la password nel test_user_data
    test_data = test_user_data.copy()
    test_data["password"] = invalid_password
    
    try:
        with timeout(30):  # Timeout di 30 secondi
            response = client.post("/api/v1/auth/register", json=test_data)
            print(f"DEBUG: Status code: {response.status_code}")
            print(f"DEBUG: Risposta: {response.text}")
            
            # Verifica che la risposta sia 422 (Unprocessable Entity)
            assert response.status_code == 422
            
            # Verifica che la risposta contenga un messaggio di errore appropriato
            error_data = response.json()
            assert "detail" in error_data
            
            # Verifica che l'errore sia relativo alla password e che il messaggio sia atteso
            assert any(
                ("password" in err.get("loc", []) or err.get("loc", [None])[-1] == "password")
                and (
                    any(keyword in err["msg"].lower() for keyword in [
                        "password", "uppercase", "lowercase", "digit", "special", "common", "at least", "empty"
                    ])
                )
                for err in error_data["detail"]
            )
    except TimeoutError as e:
        print(f"DEBUG: Test timeout dopo 30 secondi")
        raise
    except Exception as e:
        print(f"DEBUG: Errore durante il test")
        print(f"DEBUG: Errore: {str(e)}")
        raise

def test_create_user_duplicate_username(client: TestClient, existing_user: User):
    """Test creazione utente con username duplicato."""
    user_data = {
        "email": "new@example.com",
        "username": existing_user.username,
        "password": "Test123!@#",
        "full_name": "New User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, str)
    assert "username" in error_detail.lower()

def test_create_user_duplicate_email(client: TestClient, existing_user: User):
    """Test creazione utente con email duplicata."""
    user_data = {
        "email": existing_user.email,
        "username": "newuser",
        "password": "Test123!@#",
        "full_name": "New User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, str)
    assert "email" in error_detail.lower()

def test_read_users(client: TestClient, auth_headers: dict):
    """Test lettura lista utenti."""
    response = client.get("/api/v1/users/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_read_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test lettura singolo utente."""
    response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email

def test_read_user_not_found(client: TestClient, auth_headers: dict):
    """Test lettura utente non esistente."""
    response = client.get("/api/v1/users/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_update_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test updating a user."""
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.patch(
        f"/api/v1/users/{test_user.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]

def test_update_user_not_found(client: TestClient, auth_headers: dict):
    """Test updating a non-existent user."""
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.patch(
        "/api/v1/users/999",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 404

def test_delete_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test eliminazione utente."""
    response = client.delete(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200

def test_delete_user_not_found(client: TestClient, auth_headers: dict):
    """Test eliminazione utente non esistente."""
    response = client.delete("/api/v1/users/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_pytest_works():
    print("DEBUG: pytest funziona")
    assert 1 == 1 