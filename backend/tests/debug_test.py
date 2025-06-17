"""Script di debug per testare i componenti uno alla volta."""
import os
import sys
from pathlib import Path

# Aggiungi la directory backend al Python path
backend_dir = str(Path(__file__).parent.parent)
sys.path.append(backend_dir)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

from app.main import app
from app.models.user import User
from app.db.session import get_session
from app.utils.password import get_password_hash
from app.core.config import settings

def test_database_connection():
    """Test la connessione al database."""
    print("\n[DEBUG] Testing database connection...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("[DEBUG] Database connection successful!")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {str(e)}")
        raise

def test_database_tables():
    """Test che le tabelle necessarie esistano."""
    print("\n[DEBUG] Checking database tables...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Verifica tabella user
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user'
                )
            """))
            assert result.scalar() is True, "Table 'user' does not exist"
            
            # Verifica tabella alembic_version
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """))
            assert result.scalar() is True, "Table 'alembic_version' does not exist"
            
        print("[DEBUG] All required tables exist!")
    except Exception as e:
        print(f"[ERROR] Table check failed: {str(e)}")
        raise

def test_user_creation():
    """Test la creazione di un utente."""
    print("\n[DEBUG] Testing user creation...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with Session(engine) as session:
            # Crea un utente di test
            user = User(
                email="debug@example.com",
                hashed_password=get_password_hash("testpassword"),
                is_active=True,
                full_name="Debug User"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Verifica che l'utente sia stato creato
            assert user.id is not None
            assert user.email == "debug@example.com"
            print("[DEBUG] User creation successful!")
            
            # Pulisci il database
            session.delete(user)
            session.commit()
    except Exception as e:
        print(f"[ERROR] User creation failed: {str(e)}")
        raise

def test_api_endpoints():
    """Test gli endpoint API."""
    print("\n[DEBUG] Testing API endpoints...")
    try:
        client = TestClient(app)
        
        # Test endpoint di creazione utente
        print("[DEBUG] Testing user creation endpoint...")
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "api_test@example.com",
                "password": "testpassword123",
                "full_name": "API Test User"
            }
        )
        print(f"[DEBUG] User creation response: {response.status_code}")
        print(f"[DEBUG] Response body: {response.json()}")
        
        # Test endpoint di login
        print("\n[DEBUG] Testing login endpoint...")
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "api_test@example.com",
                "password": "testpassword123"
            }
        )
        print(f"[DEBUG] Login response: {response.status_code}")
        print(f"[DEBUG] Response body: {response.json()}")
        
    except Exception as e:
        print(f"[ERROR] API test failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting debug tests...")
    
    # Esegui i test in sequenza
    test_database_connection()
    test_database_tables()
    test_user_creation()
    test_api_endpoints()
    
    print("\nDebug tests completed!")