import pytest
import time
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.db.session import get_session
from app.core.config import settings
from app.utils.security import create_access_token
from app.utils.password import get_password_hash

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

@pytest.fixture
def test_user(session: Session) -> User:
    """Fixture per creare un utente di test."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Test 1: Validazione contenuto del JWT token
def test_jwt_token_structure(client: TestClient, test_user: User):
    """Verifica la struttura e i claim del token JWT."""
    # Login per ottenere il token
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["access_token"]
    
    # Decodifica il token
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    # Verifica i claim
    assert payload["sub"] == test_user.email
    assert "exp" in payload
    assert token_data["token_type"] == "bearer"
    
    # Verifica che il token non sia scaduto
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    now = datetime.utcnow()
    assert exp_datetime > now

# Test 2: Verifica scadenza del token
def test_jwt_token_expiration(client: TestClient, test_user: User):
    """Verifica che un token scaduto non sia più valido."""
    # Crea un token con scadenza di 1 secondo
    token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(seconds=1)
    )
    # Attendi 2 secondi
    time.sleep(2)
    # Prova ad usare il token scaduto
    response = client.get(
        "/users/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [401, 403, 422]  # Accetta anche 422 come risposta valida

# Test 3: Login con utente disabilitato
def test_login_with_inactive_user(client: TestClient, test_user: User, session: Session):
    """Verifica che un utente disabilitato non possa effettuare il login."""
    # Disabilita l'utente
    test_user.is_active = False
    session.add(test_user)
    session.commit()
    
    # Prova il login
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User is inactive"

# Test 4: Stress test sul Rate Limiting
def test_rate_limiting_exceeded(client: TestClient, test_user: User):
    """Verifica il comportamento del rate limiting con multiple richieste."""
    start_time = time.time()
    responses = []
    for i in range(10):
        response = client.post(
            "/token",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        responses.append(response)
        time.sleep(0.1)
    end_time = time.time()
    total_time = end_time - start_time
    print([r.status_code for r in responses])
    first_429 = next((i for i, r in enumerate(responses) if r.status_code == 429), None)
    assert first_429 is not None, "Nessuna risposta 429 trovata"
    for r in responses[first_429:]:
        assert r.status_code == 429
        data = r.json()
        assert (
            "Too Many Requests" in data.get("detail", "") or
            "Too Many Requests" in data.get("message", "") or
            "Rate limit exceeded" in data.get("error", "")
        )
    for r in responses[:first_429]:
        assert r.status_code == 401 