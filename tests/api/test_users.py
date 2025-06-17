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

@pytest.fixture(name="session")
def session_fixture():
    """Fixture per la sessione del database di test."""
    logger.debug("Setting up test database session...")
    start_time = time.time()
    
    engine = create_engine(
        "postgresql+psycopg2://postgres:N0nn0c4rl0!!@localhost:5432/eterna_home_test?sslmode=disable",
        echo=True,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        max_overflow=10
    )
    
    try:
        SQLModel.metadata.create_all(engine)
        logger.debug("Test database tables created successfully")
        
        with Session(engine) as session:
            logger.debug("Test database session created successfully")
            yield session
            logger.debug("Cleaning up test database session...")
            session.rollback()  # Rollback any pending changes
            with engine.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.commit()
            logger.debug("Test database cleanup completed")
    except Exception as e:
        logger.error(f"Error in session fixture: {str(e)}")
        raise
    finally:
        logger.debug(f"Session fixture completed in {time.time() - start_time:.2f} seconds")

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user_create = UserCreate(
        email="test@example.com",
        password="TestPassword123!",
        full_name="Test User",
        username="testuser"
    )
    return UserService.create_user(session, user_create)

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

# Test 1.1.1: GET /users/me - Successo
def test_read_users_me(client: TestClient, test_user: User):
    """Verifica che l'endpoint /users/me restituisca i dati dell'utente autenticato."""
    # Login per ottenere il token
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "TestPassword123!"}
    )
    token = response.json()["access_token"]
    
    # Richiesta con token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
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
    """Test creazione utente con campi obbligatori mancanti"""
    print("DEBUG: Inizio test_create_user_missing_required_fields")
    start_time = time.time()
    
    try:
        # Test senza email
        print("DEBUG: Test senza email")
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "password": "Test123!@#"
        })
        print(f"DEBUG: Risposta senza email - Status: {response.status_code}")
        print(f"DEBUG: Risposta senza email - Body: {response.text}")
        assert response.status_code == 422
        assert "email" in response.json()["detail"][0]["loc"]

        # Test senza username
        print("DEBUG: Test senza username")
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!@#"
        })
        print(f"DEBUG: Risposta senza username - Status: {response.status_code}")
        print(f"DEBUG: Risposta senza username - Body: {response.text}")
        assert response.status_code == 422
        assert "username" in response.json()["detail"][0]["loc"]

        # Test senza password
        print("DEBUG: Test senza password")
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "testuser"
        })
        print(f"DEBUG: Risposta senza password - Status: {response.status_code}")
        print(f"DEBUG: Risposta senza password - Body: {response.text}")
        assert response.status_code == 422
        assert "password" in response.json()["detail"][0]["loc"]
        
        print(f"DEBUG: Test completato in {time.time() - start_time:.2f} secondi")
    except Exception as e:
        print(f"DEBUG: Errore durante il test dopo {time.time() - start_time:.2f} secondi")
        print(f"DEBUG: Errore: {str(e)}")
        raise

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

def test_create_user_duplicate_username(client: TestClient, existing_user, test_user_data):
    """Test creazione utente con username duplicato"""
    test_user_data["username"] = existing_user.username
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()

def test_create_user_duplicate_email(client: TestClient, existing_user, test_user_data):
    """Test creazione utente con email duplicata"""
    test_user_data["email"] = existing_user.email
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_read_users(client: TestClient):
    """Test lettura lista utenti."""
    # Crea alcuni utenti di test
    users = [
        {"email": f"user{i}@example.com", "password": "password123"} 
        for i in range(3)
    ]
    for user_data in users:
        client.post("/api/v1/auth/register", json=user_data)
    
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("email" in user for user in data)
    assert all("password" not in user for user in data)

def test_read_user(client: TestClient):
    """Test lettura singolo utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/auth/register", json=user_data)
    user_id = create_response.json()["id"]
    
    # Leggi l'utente creato
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert data["id"] == user_id

def test_read_user_not_found(client: TestClient):
    """Test lettura utente non esistente."""
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_update_user(client: TestClient):
    """Test aggiornamento utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/auth/register", json=user_data)
    user_id = create_response.json()["id"]
    
    # Aggiorna l'utente
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123"
    }
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    assert "password" not in data

def test_update_user_not_found(client: TestClient):
    """Test aggiornamento utente non esistente."""
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123"
    }
    response = client.put("/api/v1/users/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_delete_user(client: TestClient):
    """Test eliminazione utente."""
    # Crea un utente di test
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    create_response = client.post("/api/v1/auth/register", json=user_data)
    user_id = create_response.json()["id"]
    
    # Elimina l'utente
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204
    
    # Verifica che l'utente sia stato eliminato
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404

def test_delete_user_not_found(client: TestClient):
    """Test eliminazione utente non esistente."""
    response = client.delete("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

def test_pytest_works():
    print("DEBUG: pytest funziona")
    assert 1 == 1 