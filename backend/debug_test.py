#!/usr/bin/env python3

import os
import sys
import traceback
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

# Aggiungi la directory corrente al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.config import settings

def debug_imports():
    print("=== Inizio debug delle importazioni ===")
    
    try:
        print("1. Importando config...")
        from app.core.config import settings
        print("✓ Config importato con successo")
        print(f"  - DATABASE_URL: {settings.DATABASE_URL}")
        
        print("\n2. Importando session...")
        from app.db.session import engine, SessionLocal
        print("✓ Session importato con successo")
        print(f"  - Engine configurato: {engine.url}")
        
        print("\n3. Importando models...")
        from app.models.user import User
        print("✓ Models importato con successo")
        
        print("\n4. Importando schemas...")
        from app.schemas.user import UserCreate
        print("✓ Schemas importato con successo")
        
        print("\n5. Importando main...")
        from app.main import app
        print("✓ Main importato con successo")
        
        print("\n6. Importando test dependencies...")
        from fastapi.testclient import TestClient
        print("✓ Test dependencies importate con successo")
        
        print("\n=== Tutte le importazioni completate con successo ===")
        
    except Exception as e:
        print("\n❌ ERRORE durante l'importazione:")
        print(f"Tipo di errore: {type(e).__name__}")
        print(f"Messaggio: {str(e)}")
        print("\nTraceback completo:")
        traceback.print_exc()
        sys.exit(1)

def debug_test():
    """Debug test failures."""
    print("\n[DEBUG] Starting test debugging...")
    
    # Create test client
    client = TestClient(app)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User"
    }
    
    # Test 1: Register user
    print("\n[DEBUG] Testing user registration...")
    try:
        response = client.post("/api/v1/auth/register", json=test_user)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code != 404 else 'Not Found'}")
    except Exception as e:
        print(f"Error: {type(e).__name__}")
        print(f"Error message: {str(e)}")
    
    # Test 2: Login
    print("\n[DEBUG] Testing login...")
    try:
        response = client.post(
            "/api/v1/auth/token",
            data={"username": test_user["email"], "password": test_user["password"]}
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code != 404 else 'Not Found'}")
    except Exception as e:
        print(f"Error: {type(e).__name__}")
        print(f"Error message: {str(e)}")
    
    # Test 3: Get current user
    print("\n[DEBUG] Testing get current user...")
    try:
        response = client.get("/api/v1/auth/me")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code != 404 else 'Not Found'}")
    except Exception as e:
        print(f"Error: {type(e).__name__}")
        print(f"Error message: {str(e)}")
    
    print("\n[DEBUG] Test debugging completed")

def test_user_creation():
    client = TestClient(app)
    
    # Test creazione utente
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "password": "Test123!@#",
            "full_name": "Test User"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response

if __name__ == "__main__":
    debug_imports()
    debug_test()
    test_user_creation() 