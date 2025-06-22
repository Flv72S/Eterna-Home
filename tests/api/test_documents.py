import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
import io
import hashlib

from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.security import get_password_hash

def create_test_user(db_session: Session) -> User:
    """Crea un utente di test."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role="owner"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_upload_document_file(client: TestClient, db_session):
    """Test upload di un file valido."""
    # Crea un utente e una casa
    user = create_test_user(db_session)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea un documento
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="test/path",
        checksum="test_checksum",
        house_id=house.id,
        owner_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Crea un file di test
    file_content = b"Test file content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.txt", file, "text/plain")}
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Upload del file
    response = client.post(
        f"/api/v1/documents/{document.id}/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "checksum" in data
    
    # Verifica che il checksum sia corretto
    expected_checksum = hashlib.sha256(file_content).hexdigest()
    assert data["checksum"] == expected_checksum

def test_upload_document_file_not_found(client: TestClient, db_session):
    """Test upload su documento non esistente."""
    # Crea un utente
    create_test_user(db_session)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Upload del file
    file_content = b"Test file content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.txt", file, "text/plain")}
    
    response = client.post(
        "/api/v1/documents/999/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Documento non trovato"

def test_upload_document_file_duplicate(client: TestClient, db_session):
    """Test upload doppio su stesso documento."""
    # Crea un utente e una casa
    user = create_test_user(db_session)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea un documento con file già caricato
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="test/path",
        checksum="test_checksum",
        house_id=house.id,
        owner_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Upload del file
    file_content = b"Test file content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.txt", file, "text/plain")}
    
    response = client.post(
        f"/api/v1/documents/{document.id}/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Il documento ha già un file associato"

def test_download_document_file(client: TestClient, db_session):
    """Test download di un file esistente."""
    # Crea un utente e una casa
    user = create_test_user(db_session)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea un documento con file
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="test/path",
        checksum="test_checksum",
        house_id=house.id,
        owner_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f'attachment; filename="{document.name}"'

def test_download_document_file_not_found(client: TestClient, db_session):
    """Test download di un file non esistente."""
    # Crea un utente
    create_test_user(db_session)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        "/api/v1/documents/999/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Documento non trovato"

def test_download_document_file_no_file(client: TestClient, db_session):
    """Test download di un documento senza file."""
    # Crea un utente e una casa
    user = create_test_user(db_session)
    
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=user.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    
    # Crea un documento senza file
    document = Document(
        name="Test Document",
        type="application/pdf",
        size=1024,
        path="test/path",
        checksum="test_checksum",
        house_id=house.id,
        owner_id=user.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Nessun file associato al documento" 