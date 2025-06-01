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

@pytest.fixture(name="user_create")
def user_create_fixture():
    return UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User",
        username="testuser"
    )

@pytest.fixture(name="user")
def user_fixture(session: Session, user_create: UserCreate):
    return UserService.create_user(session, user_create)

# Test 1.2.3.1: POST /users - Success
def test_create_user_success(client: TestClient, user_create: UserCreate):
    response = client.post("/users/", json=user_create.model_dump())
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_create.email
    assert data["full_name"] is None  # full_name è opzionale, quindi può essere None
    assert data["username"] == user_create.username
    assert "id" in data
    assert "hashed_password" not in data

# Test 1.2.3.2: POST /users - Duplicate
def test_create_user_duplicate_email(client: TestClient, user: User, user_create: UserCreate):
    response = client.post("/users/", json=user_create.model_dump())
    assert response.status_code == 409
    assert response.json()["detail"] == "Email già registrata"

# Test 1.2.3.3: GET /users/{id} - Success
def test_get_user_success(client: TestClient, user: User):
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert data["username"] == user.username  # Verifica che username sia incluso
    assert "hashed_password" not in data

# Test 1.2.3.3: GET /users/{id} - Not Found
def test_get_user_not_found(client: TestClient):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utente non trovato"

# Test di paginazione su GET /users
def test_get_users_pagination(client: TestClient, session: Session):
    # Crea 15 utenti di test
    users = []
    for i in range(15):
        user_create = UserCreate(
            email=f"test{i}@example.com",
            password="testpassword123",
            full_name=f"Test User {i}",
            username=f"testuser{i}"
        )
        users.append(UserService.create_user(session, user_create))

    # Test prima pagina (limit=10)
    response = client.get("/users/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["email"] == users[0].email

    # Test seconda pagina (skip=10, limit=10)
    response = client.get("/users/?skip=10&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Rimangono solo 5 utenti
    assert data[0]["email"] == users[10].email

    # Test con skip maggiore del numero totale
    response = client.get("/users/?skip=20&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

# Test PUT /users/{id}
def test_update_user_success(client: TestClient, user: User):
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = client.put(f"/users/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]

# Test DELETE /users/{id}
def test_delete_user_success(client: TestClient, user: User):
    response = client.delete(f"/users/{user.id}")
    assert response.status_code == 204

    # Verifica che l'utente sia stato effettivamente eliminato
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 404 