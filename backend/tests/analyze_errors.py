import pytest
import sys
from fastapi.testclient import TestClient
from app.main import app

def analyze_test_errors():
    """Analyze test errors and provide detailed information."""
    print("\n[DEBUG] Starting test analysis...")
    
    # Create test client
    client = TestClient(app)
    
    # Test endpoints
    endpoints = [
        ("/api/v1/auth/register", "POST"),
        ("/api/v1/auth/token", "POST"),
        ("/api/v1/auth/me", "GET")
    ]
    
    # Check each endpoint
    for endpoint, method in endpoints:
        print(f"\n[DEBUG] Checking endpoint: {method} {endpoint}")
        try:
            if method == "POST":
                response = client.post(endpoint, json={
                    "email": "test@example.com",
                    "password": "Test123!@#",
                    "full_name": "Test User"
                })
            else:
                response = client.get(endpoint)
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.json() if response.status_code != 404 else 'Not Found'}")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}")
            print(f"Error message: {str(e)}")
    
    print("\n[DEBUG] Test analysis completed")

if __name__ == "__main__":
    analyze_test_errors() 