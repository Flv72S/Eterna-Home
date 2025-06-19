TEST_USER = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "TestPassword123!",
    "full_name": "Test User"
}

import pytest
from sqlalchemy import inspect, text

def test_login_success(client, db_session):
    """Test successful login."""
    # Debug: info database
    print("[DEBUG] DB URL:", db_session.bind.url)
    result = db_session.execute(text("SHOW search_path;"))
    print("[DEBUG] search_path:", result.fetchone())
    inspector = inspect(db_session.bind)
    print("[DEBUG] Tabelle visibili:", inspector.get_table_names())

    # Debug: chiama /debug-db e stampa il risultato
    debug_resp = client.get("/debug-db")
    print(f"[DEBUG] /debug-db: {debug_resp.json()}")

    # Register user first
    reg_response = client.post("/api/v1/auth/register", json=TEST_USER)
    reg_status = reg_response.status_code
    reg_json = reg_response.json()
    print(f"[DEBUG] Register response status: {reg_status}")
    print(f"[DEBUG] Register response json: {reg_json}")

    # Try to login
    response = client.post(
        "/api/v1/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    login_status = response.status_code
    login_json = response.json()
    print(f"[DEBUG] Login response status: {login_status}")
    print(f"[DEBUG] Login response json: {login_json}")
    
    assert login_status == 200 