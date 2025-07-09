import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.utils.password import get_password_hash
from sqlmodel import Session
from app.database import get_db, engine

client = TestClient(app)

# Credenziali di test
USERS = [
    {
        "email": "admin_rbac_test@example.com",
        "username": "admin_rbac_test",
        "password": "AdminTest123!",
        "role": "admin"
    },
    {
        "email": "guest_rbac_test@example.com",
        "username": "guest_rbac_test",
        "password": "GuestTest123!",
        "role": "guest"
    },
    {
        "email": "tech_rbac_test@example.com",
        "username": "tech_rbac_test",
        "password": "TechTest123!",
        "role": "technician"
    }
]

def setup_test_users(db_session):
    """Crea utenti di test se non esistono"""
    for u in USERS:
        user = db_session.exec(
            db_session.query(User).filter(User.email == u["email"]).statement
        ).first()
        if not user:
            user = User(
                email=u["email"],
                username=u["username"],
                hashed_password=get_password_hash(u["password"]),
                is_active=True,
                role=u["role"]
            )
            db_session.add(user)
    db_session.commit()

def login(client, email, password):
    response = client.post(
        "/api/v1/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed for {email}"
    return response.json()["access_token"]

def test_admin_access(client, db_session):
    setup_test_users(db_session)
    token = login(client, "admin_rbac_test@example.com", "AdminTest123!")
    # Accesso consentito
    r = client.get("/api/v1/secure-area/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    # Accesso dinamico
    r2 = client.get("/api/v1/secure-area/role-test/admin", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    # Accesso negato a super-admin-only
    r3 = client.get("/api/v1/secure-area/super-admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 403

def test_guest_access(client, db_session):
    setup_test_users(db_session)
    token = login(client, "guest_rbac_test@example.com", "GuestTest123!")
    # Accesso negato
    r = client.get("/api/v1/secure-area/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    # Accesso consentito a user-only
    r2 = client.get("/api/v1/secure-area/user-only", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    # Accesso negato a technician-only
    r3 = client.get("/api/v1/secure-area/technician-only", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 403

def test_technician_access(client, db_session):
    setup_test_users(db_session)
    token = login(client, "tech_rbac_test@example.com", "TechTest123!")
    # Accesso consentito a technician-only
    r = client.get("/api/v1/secure-area/technician-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    # Accesso negato a admin-only
    r2 = client.get("/api/v1/secure-area/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403
    # Accesso dinamico
    r3 = client.get("/api/v1/secure-area/role-test/technician", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200 