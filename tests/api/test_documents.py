"""Test per gli endpoint dei documenti."""
import io
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User
from app.models.house import House
from app.models.document import Document


def test_upload_document_file(client: TestClient, auth_test_session, test_user_auth):
    """Test upload di un file su un documento esistente."""
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=test_user_auth.id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento
    document = Document(
        title="Test Document",
        file_type="application/pdf",
        file_size=1024,
        file_url="test/path",
        checksum="test_checksum",
        owner_id=test_user_auth.id,
        house_id=house.id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Prepara il file per l'upload
    file_content = b"Test file content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.txt", file, "text/plain")}
    
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
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

def test_upload_document_file_not_found(client: TestClient, auth_test_session, test_user_auth):
    """Test upload su documento non esistente."""
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
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

def test_upload_document_file_duplicate(client: TestClient, auth_test_session, test_user_auth):
    """Test upload doppio su stesso documento."""
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=test_user_auth.id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento con file già caricato
    document = Document(
        title="Test Document",
        file_type="application/pdf",
        file_size=1024,
        file_url="test/path",
        checksum="test_checksum",
        owner_id=test_user_auth.id,
        house_id=house.id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
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

def test_download_document_file(client: TestClient, auth_test_session, test_user_auth):
    """Test download di un file esistente."""
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=test_user_auth.id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento con file
    document = Document(
        title="Test Document",
        file_type="application/pdf",
        file_size=1024,
        file_url="test/path",
        checksum="test_checksum",
        owner_id=test_user_auth.id,
        house_id=house.id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f'attachment; filename="{document.title}"'

def test_download_document_file_not_found(client: TestClient, auth_test_session, test_user_auth):
    """Test download di un file non esistente."""
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        "/api/v1/documents/999/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Documento non trovato"

def test_download_document_file_no_file(client: TestClient, auth_test_session, test_user_auth):
    """Test download di un documento senza file."""
    # Crea una casa
    house = House(
        name="Test House",
        address="123 Test Street",
        owner_id=test_user_auth.id
    )
    auth_test_session.add(house)
    auth_test_session.commit()
    auth_test_session.refresh(house)
    
    # Crea un documento senza file
    document = Document(
        title="Test Document",
        file_type="application/pdf",
        file_size=1024,
        file_url="test/path",
        checksum="test_checksum",
        owner_id=test_user_auth.id,
        house_id=house.id
    )
    auth_test_session.add(document)
    auth_test_session.commit()
    auth_test_session.refresh(document)
    
    # Login
    login_response = client.post(
        "/api/v1/token",
        data={"username": test_user_auth.email, "password": "TestPassword123!"}
    )
    token = login_response.json()["access_token"]
    
    # Download del file
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "File non trovato" 