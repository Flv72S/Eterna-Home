import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text
import time

from app.main import app
from app.models.user import User
from app.db.session import get_session
from app.utils.password import get_password_hash
from app.core.config import settings

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
}

TEST_USER_DUPLICATE = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Another User"
}

TEST_USER_INVALID_EMAIL = {
    "email": "invalid-email",
    "password": "Test123!@#",
    "full_name": "Invalid User"
}

TEST_USER_WEAK_PASSWORD = {
    "email": "weak@example.com",
    "password": "weak",
    "full_name": "Weak User"
}

TEST_USER_MISSING_FIELDS = {
    "email": "missing@example.com"
    # password e full_name mancanti
}

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        # Cleanup
        session.execute(text("DELETE FROM \"user\" CASCADE"))
        session.commit()

def test_user_creation_required_fields(client, db_session):
    """Test validazione dati obbligatori."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_MISSING_FIELDS)
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data["detail"])
    assert "full_name" in str(data["detail"])

def test_user_creation_email_validation(client, db_session):
    """Test validazione formato email."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_INVALID_EMAIL)
    assert response.status_code == 422
    data = response.json()
    assert "email" in str(data["detail"])

def test_user_creation_password_validation(client, db_session):
    """Test validazione password."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_WEAK_PASSWORD)
    assert response.status_code == 422
    data = response.json()
    assert "password" in str(data["detail"])

def test_user_creation_duplicate_email(client, db_session):
    """Test gestione email duplicata."""
    # Prima registrazione
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Seconda registrazione con stessa email
    response = client.post("/api/v1/auth/register", json=TEST_USER_DUPLICATE)
    assert response.status_code == 400
    assert "Email già registrata" in response.json()["detail"]

def test_user_profile_authentication(client, db_session):
    """Test autenticazione richiesta per profilo utente."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_user_profile_data(client, db_session):
    """Test dati completi restituiti nel profilo utente."""
    # Registra e login
    client.post("/api/v1/auth/register", json=TEST_USER)
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Recupera profilo
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "id" in data
    assert "username" in data

def test_user_profile_invalid_token(client, db_session):
    """Test gestione token non valido."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_login_valid_credentials(client, db_session):
    """Test login con credenziali valide."""
    # Registra utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, db_session):
    """Test login con credenziali non valide."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def test_login_disabled_account(client, db_session):
    """Test login con account disabilitato."""
    # Crea utente disabilitato
    user = User(
        email=TEST_USER["email"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Prova login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def test_login_rate_limit(client, db_session):
    """Test rate limiting sul login."""
    # Registra utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Prova login 6 volte (dovrebbe fallire al 6° tentativo)
    for i in range(6):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
        )
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "Troppi tentativi di login" in response.json()["detail"]
        time.sleep(0.1)  # Piccola pausa tra i tentativi 