import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.user import User
from app.utils.password import get_password_hash
from app.main import app

# Dati di test
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
}

TEST_USER_DUPLICATE = {
    "email": "test@example.com",  # Email duplicata
    "password": "Test123!@#",
    "full_name": "Test User 2"
}

TEST_USER_INVALID_EMAIL = {
    "email": "invalid-email",
    "password": "Test123!@#",
    "full_name": "Test User 3"
}

TEST_USER_WEAK_PASSWORD = {
    "email": "test2@example.com",
    "password": "weak",
    "full_name": "Test User 4"
}

TEST_USER_MISSING_FIELDS = {
    "email": "test3@example.com"
    # Password e full_name mancanti
}

@pytest.fixture
def client():
    return TestClient(app)

# Test POST /api/users/ - Creazione nuovo utente
def test_create_user_success(client: TestClient, db_session: Session):
    """Test creazione utente con successo."""
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "hashed_password" not in data
    assert data["is_active"] is True

def test_create_user_duplicate_email(client: TestClient, db_session: Session):
    """Test creazione utente con email duplicata."""
    # Crea primo utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Prova a creare secondo utente con stessa email
    response = client.post("/api/v1/auth/register", json=TEST_USER_DUPLICATE)
    assert response.status_code == 400
    assert "email già registrata" in response.json()["detail"].lower()

def test_create_user_invalid_email(client: TestClient, db_session: Session):
    """Test creazione utente con email non valida."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_INVALID_EMAIL)
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_create_user_weak_password(client: TestClient, db_session: Session):
    """Test creazione utente con password debole."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_WEAK_PASSWORD)
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]

def test_create_user_missing_fields(client: TestClient, db_session: Session):
    """Test creazione utente con campi obbligatori mancanti."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_MISSING_FIELDS)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("password" in error["loc"] for error in errors)
    assert any("full_name" in error["loc"] for error in errors)

# Test GET /api/users/me - Recupero profilo utente corrente
def test_get_current_user_success(client: TestClient, db_session: Session):
    """Test recupero profilo utente con autenticazione valida."""
    # Crea utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Login per ottenere token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Recupera profilo
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "hashed_password" not in data
    assert data["is_active"] is True

def test_get_current_user_no_auth(client: TestClient):
    """Test recupero profilo utente senza autenticazione."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_get_current_user_invalid_token(client: TestClient):
    """Test recupero profilo utente con token non valido."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

# Test POST /api/auth/login - Login utente
def test_login_success(client: TestClient, db_session: Session):
    """Test login con credenziali valide."""
    # Crea utente
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

def test_login_invalid_credentials(client: TestClient, db_session: Session):
    """Test login con credenziali non valide."""
    # Crea utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Login con password errata
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def test_login_disabled_account(client: TestClient, db_session: Session):
    """Test login con account disabilitato."""
    # Crea utente disabilitato
    user = User(
        email=TEST_USER["email"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_active=False,
        full_name=TEST_USER["full_name"]
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

def test_login_rate_limiting(client: TestClient, db_session: Session):
    """Test rate limiting per login."""
    # Crea utente
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Prova login multiple volte
    for _ in range(6):  # Assumendo un limite di 5 tentativi
        response = client.post(
            "/api/v1/auth/token",
            data={"username": TEST_USER["email"], "password": "wrongpassword"}
        )
    
    # L'ultima richiesta dovrebbe essere bloccata
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"] 