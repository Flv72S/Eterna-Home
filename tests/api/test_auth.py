import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session

# Configurazione del database di test
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

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
        password="testpassword123",
        full_name="Test User",
        username="testuser"
    )
    return UserService.create_user(session, user_create)

# Test 1.3.1.1: Verifica hashing password
def test_password_hashing(test_user: User):
    """Verifica che la password sia stata hashata correttamente."""
    assert test_user.hashed_password != "testpassword123"
    assert test_user.hashed_password.startswith("$2b$")  # Verifica che sia un hash bcrypt

# Test 1.3.1.2: POST /token - Successo
def test_login_success(client: TestClient, test_user: User):
    """Verifica che il login con credenziali valide restituisca un token JWT."""
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

# Test 1.3.1.3: POST /token - Credenziali errate
def test_login_invalid_credentials(client: TestClient, test_user: User):
    """Verifica che il login con credenziali errate restituisca errore 401."""
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenziali non valide"

# Test di integrazione: Rate limiting
def test_rate_limiting(client: TestClient, test_user: User):
    """Verifica che il rate limiting blocchi troppe richieste consecutive."""
    # Esegui 6 richieste consecutive (limite è 5/minuto)
    for _ in range(6):
        response = client.post(
            "/token",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
    
    # La sesta richiesta dovrebbe essere bloccata
    print("Rate limit response:", response.json())
    assert response.status_code == 429
    # assert "Too Many Requests" in response.json()["detail"] 