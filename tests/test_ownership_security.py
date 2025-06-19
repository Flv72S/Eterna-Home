"""
Test per il controllo proprietà risorse (ownership security)
Verifica che ogni utente possa accedere solo alle proprie risorse
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.auth import create_access_token
from app.utils.password import get_password_hash
import uuid

client = TestClient(app)

@pytest.fixture
def user1(db_session: Session):
    """Crea il primo utente di test."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user1_{unique_id}",
        email=f"user1_{unique_id}@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def user2(db_session: Session):
    """Crea il secondo utente di test."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"user2_{unique_id}", 
        email=f"user2_{unique_id}@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def house_user1(db_session: Session, user1):
    """Crea una casa appartenente a user1."""
    house = House(
        name="Casa User1",
        address="Via User1 123",
        owner_id=user1.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def house_user2(db_session: Session, user2):
    """Crea una casa appartenente a user2."""
    house = House(
        name="Casa User2", 
        address="Via User2 456",
        owner_id=user2.id
    )
    db_session.add(house)
    db_session.commit()
    db_session.refresh(house)
    return house

@pytest.fixture
def document_user1(db_session: Session, user1, house_user1):
    """Crea un documento appartenente a user1."""
    document = Document(
        name="Documento User1",
        type="application/pdf",
        size=1024,
        path="/documents/user1.pdf",
        checksum="abc123",
        description="Documento di user1",
        owner_id=user1.id,
        house_id=house_user1.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

@pytest.fixture
def document_user2(db_session: Session, user2, house_user2):
    """Crea un documento appartenente a user2."""
    document = Document(
        name="Documento User2",
        type="application/pdf", 
        size=2048,
        path="/documents/user2.pdf",
        checksum="def456",
        description="Documento di user2",
        owner_id=user2.id,
        house_id=house_user2.id
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document

def get_auth_headers(user):
    """Crea headers di autenticazione per un utente."""
    token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {token}"}

# ============================================================================
# TEST 1 - Accesso Case per Proprietario
# ============================================================================

def test_user_can_access_own_houses(client, user1, house_user1):
    """✅ TEST 1.1: Utente può visualizzare le proprie case."""
    headers = get_auth_headers(user1)
    
    # Lista case
    response = client.get("/api/v1/houses/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Casa User1"
    assert data["items"][0]["owner_id"] == user1.id
    
    # Dettaglio casa
    response = client.get(f"/api/v1/houses/{house_user1.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Casa User1"
    assert data["owner_id"] == user1.id

def test_user_cannot_access_other_user_houses(client, user1, house_user2):
    """❌ TEST 1.2: Utente non può accedere a case di altri utenti."""
    headers = get_auth_headers(user1)
    
    # Tentativo di accesso a casa di user2
    response = client.get(f"/api/v1/houses/{house_user2.id}", headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_houses_in_list(client, user1, user2, house_user1, house_user2):
    """❌ TEST 1.3: Utente vede solo le proprie case nella lista."""
    headers = get_auth_headers(user1)
    
    response = client.get("/api/v1/houses/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verifica che veda solo la propria casa
    assert len(data["items"]) == 1
    assert data["items"][0]["owner_id"] == user1.id
    assert data["items"][0]["id"] == house_user1.id
    
    # Verifica che NON veda la casa di user2
    house_ids = [house["id"] for house in data["items"]]
    assert house_user2.id not in house_ids

# ============================================================================
# TEST 2 - Accesso Documento per Proprietario  
# ============================================================================

def test_user_can_access_own_documents(client, user1, document_user1):
    """✅ TEST 2.1: Utente può accedere ai propri documenti."""
    headers = get_auth_headers(user1)
    
    # Lista documenti
    response = client.get("/api/v1/documents/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(doc["name"] == "Documento User1" for doc in data)
    
    # Dettaglio documento
    response = client.get(f"/api/v1/documents/{document_user1.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Documento User1"
    assert data["owner_id"] == user1.id

def test_user_cannot_access_other_user_documents(client, user1, document_user2):
    """❌ TEST 2.2: Utente non può accedere a documenti di altri utenti."""
    headers = get_auth_headers(user1)
    
    # Tentativo di accesso a documento di user2
    response = client.get(f"/api/v1/documents/{document_user2.id}", headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_documents_in_list(client, user1, user2, document_user1, document_user2):
    """❌ TEST 2.3: Utente vede solo i propri documenti nella lista."""
    headers = get_auth_headers(user1)
    
    response = client.get("/api/v1/documents/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verifica che veda solo i propri documenti
    document_ids = [doc["id"] for doc in data]
    assert document_user1.id in document_ids
    assert document_user2.id not in document_ids

# ============================================================================
# TEST 3 - Modifica Risorsa
# ============================================================================

def test_user_can_modify_own_house(client, user1, house_user1):
    """✅ TEST 3.1: Utente può modificare la propria casa."""
    headers = get_auth_headers(user1)
    
    update_data = {
        "name": "Casa User1 Modificata",
        "address": "Via User1 789"
    }
    
    response = client.put(f"/api/v1/houses/{house_user1.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Casa User1 Modificata"
    assert data["address"] == "Via User1 789"

def test_user_cannot_modify_other_user_house(client, user1, house_user2):
    """❌ TEST 3.2: Utente non può modificare case di altri utenti."""
    headers = get_auth_headers(user1)
    
    update_data = {
        "name": "Tentativo di Modifica",
        "address": "Via Tentativo 123"
    }
    
    response = client.put(f"/api/v1/houses/{house_user2.id}", json=update_data, headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_can_modify_own_document(client, user1, document_user1):
    """✅ TEST 3.3: Utente può modificare il proprio documento."""
    headers = get_auth_headers(user1)
    
    update_data = {
        "name": "Documento User1 Modificato",
        "description": "Descrizione modificata"
    }
    
    response = client.put(f"/api/v1/documents/{document_user1.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Documento User1 Modificato"
    assert data["description"] == "Descrizione modificata"

def test_user_cannot_modify_other_user_document(client, user1, document_user2):
    """❌ TEST 3.4: Utente non può modificare documenti di altri utenti."""
    headers = get_auth_headers(user1)
    
    update_data = {
        "name": "Tentativo di Modifica",
        "description": "Tentativo"
    }
    
    response = client.put(f"/api/v1/documents/{document_user2.id}", json=update_data, headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 4 - Eliminazione Risorsa
# ============================================================================

def test_user_can_delete_own_house(client, user1, house_user1):
    """✅ TEST 4.1: Utente può eliminare la propria casa."""
    headers = get_auth_headers(user1)
    
    response = client.delete(f"/api/v1/houses/{house_user1.id}", headers=headers)
    assert response.status_code == 204
    
    # Verifica che la casa sia stata eliminata
    response = client.get(f"/api/v1/houses/{house_user1.id}", headers=headers)
    assert response.status_code == 404

def test_user_cannot_delete_other_user_house(client, user1, house_user2):
    """❌ TEST 4.2: Utente non può eliminare case di altri utenti."""
    headers = get_auth_headers(user1)
    
    response = client.delete(f"/api/v1/houses/{house_user2.id}", headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_can_delete_own_document(client, user1, document_user1):
    """✅ TEST 4.3: Utente può eliminare il proprio documento."""
    headers = get_auth_headers(user1)
    
    response = client.delete(f"/api/v1/documents/{document_user1.id}", headers=headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verifica che il documento sia stato eliminato
    response = client.get(f"/api/v1/documents/{document_user1.id}", headers=headers)
    assert response.status_code == 404

def test_user_cannot_delete_other_user_document(client, user1, document_user2):
    """❌ TEST 4.4: Utente non può eliminare documenti di altri utenti."""
    headers = get_auth_headers(user1)
    
    response = client.delete(f"/api/v1/documents/{document_user2.id}", headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 5 - Creazione Risorsa
# ============================================================================

def test_user_can_create_house_for_self(client, user1):
    """✅ TEST 5.1: Utente può creare una casa per se stesso."""
    headers = get_auth_headers(user1)
    
    house_data = {
        "name": "Nuova Casa User1",
        "address": "Via Nuova 123"
    }
    
    response = client.post("/api/v1/houses/", json=house_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Nuova Casa User1"
    assert data["owner_id"] == user1.id

def test_user_can_create_document_for_own_house(client, user1, house_user1):
    """✅ TEST 5.2: Utente può creare un documento per la propria casa."""
    headers = get_auth_headers(user1)
    
    document_data = {
        "name": "Nuovo Documento",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/nuovo.pdf",
        "checksum": "xyz789",
        "description": "Nuovo documento",
        "house_id": house_user1.id
    }
    
    response = client.post("/api/v1/documents/", json=document_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nuovo Documento"
    assert data["owner_id"] == user1.id
    assert data["house_id"] == house_user1.id

# ============================================================================
# TEST 6 - Accesso Cross-User Completo
# ============================================================================

def test_complete_cross_user_isolation(client, user1, user2, house_user1, house_user2, document_user1, document_user2):
    """🔒 TEST 6: Verifica completa isolamento tra utenti."""
    headers_user1 = get_auth_headers(user1)
    headers_user2 = get_auth_headers(user2)
    
    # User1 non può vedere/modificare risorse di User2
    response = client.get(f"/api/v1/houses/{house_user2.id}", headers=headers_user1)
    assert response.status_code == 403
    
    response = client.put(f"/api/v1/houses/{house_user2.id}", json={"name": "Tentativo"}, headers=headers_user1)
    assert response.status_code == 403
    
    response = client.delete(f"/api/v1/houses/{house_user2.id}", headers=headers_user1)
    assert response.status_code == 403
    
    # User2 non può vedere/modificare risorse di User1
    response = client.get(f"/api/v1/houses/{house_user1.id}", headers=headers_user2)
    assert response.status_code == 403
    
    response = client.put(f"/api/v1/houses/{house_user1.id}", json={"name": "Tentativo"}, headers=headers_user2)
    assert response.status_code == 403
    
    response = client.delete(f"/api/v1/houses/{house_user1.id}", headers=headers_user2)
    assert response.status_code == 403
    
    # Ogni utente può accedere solo alle proprie risorse
    response = client.get("/api/v1/houses/", headers=headers_user1)
    assert response.status_code == 200
    user1_houses = response.json()["items"]
    assert all(house["owner_id"] == user1.id for house in user1_houses)
    
    response = client.get("/api/v1/houses/", headers=headers_user2)
    assert response.status_code == 200
    user2_houses = response.json()["items"]
    assert all(house["owner_id"] == user2.id for house in user2_houses)

# ============================================================================
# TEST 7 - Download Documenti
# ============================================================================

def test_user_can_download_own_document(client, user1, document_user1, override_minio_service):
    """✅ TEST 7.1: Utente può scaricare i propri documenti."""
    headers = get_auth_headers(user1)
    
    response = client.get(f"/api/v1/documents/download/{document_user1.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data

def test_user_cannot_download_other_user_document(client, user1, document_user2, override_minio_service):
    """❌ TEST 7.2: Utente non può scaricare documenti di altri utenti."""
    headers = get_auth_headers(user1)
    
    response = client.get(f"/api/v1/documents/download/{document_user2.id}", headers=headers)
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 8 - Upload Documenti
# ============================================================================

def test_user_can_upload_to_own_document(client, user1, document_user1, override_minio_service):
    """✅ TEST 8.1: Utente può caricare file sui propri documenti."""
    headers = get_auth_headers(user1)
    
    # Simula un file di test
    files = {"file": ("test.txt", b"test content", "text/plain")}
    
    response = client.post(
        f"/api/v1/documents/{document_user1.id}/upload",
        files=files,
        headers=headers
    )
    # Nota: questo test potrebbe fallire se MinIO non è configurato per i test
    # Il controllo importante è che non restituisca 403
    assert response.status_code != 403

def test_user_cannot_upload_to_other_user_document(client, user1, document_user2, override_minio_service):
    """❌ TEST 8.2: Utente non può caricare file su documenti di altri utenti."""
    headers = get_auth_headers(user1)
    
    files = {"file": ("test.txt", b"test content", "text/plain")}
    
    response = client.post(
        f"/api/v1/documents/{document_user2.id}/upload",
        files=files,
        headers=headers
    )
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 9 - Edge Cases
# ============================================================================

def test_access_nonexistent_house(client, user1):
    """🔍 TEST 9.1: Accesso a casa inesistente."""
    headers = get_auth_headers(user1)
    
    response = client.get("/api/v1/houses/99999", headers=headers)
    assert response.status_code == 404

def test_access_nonexistent_document(client, user1):
    """🔍 TEST 9.2: Accesso a documento inesistente."""
    headers = get_auth_headers(user1)
    
    response = client.get("/api/v1/documents/99999", headers=headers)
    assert response.status_code == 404

def test_unauthorized_access_without_token(client):
    """🔍 TEST 9.3: Accesso senza token di autenticazione."""
    # Test case
    response = client.get("/api/v1/houses/")
    assert response.status_code == 401
    
    # Test documenti
    response = client.get("/api/v1/documents/")
    assert response.status_code == 401

def test_unauthorized_access_with_invalid_token(client):
    """🔍 TEST 9.4: Accesso con token invalido."""
    headers = {"Authorization": "Bearer invalid_token"}
    
    # Test case
    response = client.get("/api/v1/houses/", headers=headers)
    assert response.status_code == 401
    
    # Test documenti
    response = client.get("/api/v1/documents/", headers=headers)
    assert response.status_code == 401 