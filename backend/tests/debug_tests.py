import pytest
import sys
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

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

TEST_USER_WEAK_PASSWORD = {
    "email": "test2@example.com",
    "password": "weak",
    "full_name": "Test User 2"
}

TEST_USER_INVALID_EMAIL = {
    "email": "invalid-email",
    "password": "Test123!@#",
    "full_name": "Test User 3"
}

def setup_test_environment():
    """Setup test environment."""
    print("\n[DEBUG] Setting up test environment...")
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    return engine

def cleanup_test_environment(engine):
    """Cleanup test environment."""
    print("\n[DEBUG] Cleaning up test environment...")
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM \"user\" CASCADE"))
        conn.commit()

def run_test(test_func, *args, **kwargs):
    """Run a single test and capture its output."""
    print(f"\n[DEBUG] Running test: {test_func.__name__}")
    try:
        test_func(*args, **kwargs)
        print(f"[SUCCESS] Test {test_func.__name__} passed")
    except Exception as e:
        print(f"[ERROR] Test {test_func.__name__} failed")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.json() if hasattr(e.response, 'json') else e.response.text}")

def test_register_user_success(client, db_session):
    """Test successful user registration."""
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "id" in data
    assert data["username"] is not None

def test_register_user_duplicate_email(client, db_session):
    """Test registration with duplicate email."""
    client.post("/api/v1/auth/register", json=TEST_USER)
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert "Email già registrata" in response.json()["detail"]

def test_register_user_invalid_email(client, db_session):
    """Test registration with invalid email."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_INVALID_EMAIL)
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_register_user_weak_password(client, db_session):
    """Test registration with weak password."""
    response = client.post("/api/v1/auth/register", json=TEST_USER_WEAK_PASSWORD)
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]

def test_login_success(client, db_session):
    """Test successful login."""
    client.post("/api/v1/auth/register", json=TEST_USER)
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_disabled_account(client, db_session):
    """Test login with disabled account."""
    user = User(
        email=TEST_USER["email"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 401
    assert "Credenziali non valide" in response.json()["detail"]

def main():
    """Main function to run all tests."""
    print("[DEBUG] Starting test debugging...")
    
    # Setup
    engine = setup_test_environment()
    client = TestClient(app)
    db_session = Session(engine)
    
    try:
        # Run each test individually
        tests = [
            test_register_user_success,
            test_register_user_duplicate_email,
            test_register_user_invalid_email,
            test_register_user_weak_password,
            test_login_success,
            test_login_disabled_account
        ]
        
        for test in tests:
            run_test(test, client, db_session)
            cleanup_test_environment(engine)
            
    finally:
        # Cleanup
        cleanup_test_environment(engine)
        db_session.close()
        print("\n[DEBUG] Test debugging completed")

if __name__ == "__main__":
    main() 