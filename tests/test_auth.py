TEST_USER = {
    "email": "testuser@example.com",
    "password": "testpassword123"
}

import pytest

def test_login_success(client, db_session):
    """Test successful login."""
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