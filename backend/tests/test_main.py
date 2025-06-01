import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Eterna Home API"}

def test_read_users():
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"testuser_{unique}",
        "email": f"test_{unique}@example.com",
        "password": "testpassword123",
        "is_active": True,
        "is_superuser": False
    }
    response = client.post("/api/v1/users/", json=user_data)
    if response.status_code != 200:
        print(f"Response body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data

