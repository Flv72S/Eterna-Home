"""
Test per il controllo proprietà risorse (ownership security)
Verifica che ogni utente possa accedere solo alle proprie risorse
"""
import pytest
import time
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models.user import User
from app.models.house import House
from app.models.document import Document
from app.core.auth import create_access_token
from app.utils.password import get_password_hash
import uuid
from app.models.enums import UserRole

def get_auth_headers(client, user):
    """Crea headers di autenticazione per un utente tramite login reale."""
    # Usa l'endpoint di login reale invece di creare token direttamente
    response = client.post(
        "/api/v1/token",
        data={"username": user["email"], "password": "TestPassword123!"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def user1(client):
    """Crea user1 tramite API di registrazione."""
    timestamp = int(time.time() * 1000)
    email = f"user1_{timestamp}@example.com"
    password = "TestPassword123!"
    data = {
        "email": email,
        "username": f"user1_{timestamp}",
        "password": password,
        "full_name": "User One",
        "role": UserRole.get_default_role(),
        "is_active": True
    }
    response = client.post("/api/v1/register", json=data)
    assert response.status_code in (200, 201), f"Registration failed: {response.text}"
    user_data = response.json()
    
    # Login per ottenere token
    login_response = client.post(
        "/api/v1/token",
        data={"username": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {
        "id": user_data["id"],
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }

@pytest.fixture(scope="module")
def user2(client):
    """Crea user2 tramite API di registrazione."""
    timestamp = int(time.time() * 1000)
    email = f"user2_{timestamp}@example.com"
    password = "TestPassword123!"
    data = {
        "email": email,
        "username": f"user2_{timestamp}",
        "password": password,
        "full_name": "User Two",
        "role": UserRole.get_default_role(),
        "is_active": True
    }
    response = client.post("/api/v1/register", json=data)
    assert response.status_code in (200, 201), f"Registration failed: {response.text}"
    user_data = response.json()
    
    # Login per ottenere token
    login_response = client.post(
        "/api/v1/token",
        data={"username": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {
        "id": user_data["id"],
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }

@pytest.fixture(scope="module")
def house_user1(client, user1):
    """Crea casa per user1 tramite API."""
    house_data = {
        "name": "Casa User1",
        "address": "Via Roma 1",
        "description": "Casa di User1"
    }
    response = client.post("/api/v1/houses/", json=house_data, headers=user1["headers"])
    assert response.status_code in (200, 201), f"House creation failed: {response.text}"
    return response.json()

@pytest.fixture(scope="module")
def house_user2(client, user2):
    """Crea casa per user2 tramite API."""
    house_data = {
        "name": "Casa User2",
        "address": "Via Milano 2",
        "description": "Casa di User2"
    }
    response = client.post("/api/v1/houses/", json=house_data, headers=user2["headers"])
    assert response.status_code in (200, 201), f"House creation failed: {response.text}"
    return response.json()

@pytest.fixture(scope="module")
def document_user1(client, user1, house_user1):
    """Crea un documento per user1 tramite API."""
    document_data = {
        "name": "Documento User1",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/user1_doc.pdf",
        "checksum": "abc123def456",
        "description": "Documento di User1",
        "house_id": house_user1["id"]
    }
    response = client.post("/api/v1/documents/", json=document_data, headers=user1["headers"])
    assert response.status_code in (200, 201), f"Document creation failed: {response.text}"
    return response.json()

@pytest.fixture(scope="module")
def document_user2(client, user2, house_user2):
    """Crea un documento per user2 tramite API."""
    document_data = {
        "name": "Documento User2",
        "type": "application/pdf",
        "size": 2048,
        "path": "/documents/user2_doc.pdf",
        "checksum": "def456ghi789",
        "description": "Documento di User2",
        "house_id": house_user2["id"]
    }
    response = client.post("/api/v1/documents/", json=document_data, headers=user2["headers"])
    assert response.status_code in (200, 201), f"Document creation failed: {response.text}"
    return response.json()

# ============================================================================
# TEST 1 - Accesso Case per Proprietario
# ============================================================================

def test_user_can_access_own_houses(client, user1, house_user1):
    """✅ TEST 1.1: Utente può visualizzare le proprie case."""
    # Lista case
    response = client.get("/api/v1/houses/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Casa User1"
    
    # Dettaglio casa
    response = client.get(f"/api/v1/houses/{house_user1['id']}", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Casa User1"

def test_user_cannot_access_other_user_houses(client, user1, house_user2):
    """❌ TEST 1.2: Utente non può accedere a case di altri utenti."""
    # Tentativo di accesso a casa di user2
    response = client.get(f"/api/v1/houses/{house_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_houses_in_list(client, user1, user2, house_user1, house_user2):
    """❌ TEST 1.3: Utente vede solo le proprie case nella lista."""
    response = client.get("/api/v1/houses/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Casa User1"
    
    # Verifica che non veda la casa di user2
    house_ids = [house["id"] for house in data["items"]]
    assert house_user2["id"] not in house_ids

# ============================================================================
# TEST 2 - Accesso Documenti per Proprietario
# ============================================================================

def test_user_can_access_own_documents(client, user1, document_user1):
    """✅ TEST 2.1: Utente può visualizzare i propri documenti."""
    # Lista documenti
    response = client.get("/api/v1/documents/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Documento User1"
    
    # Dettaglio documento
    response = client.get(f"/api/v1/documents/{document_user1['id']}", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Documento User1"

def test_user_cannot_access_other_user_documents(client, user1, document_user2):
    """❌ TEST 2.2: Utente non può accedere a documenti di altri utenti."""
    response = client.get(f"/api/v1/documents/{document_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_documents_in_list(client, user1, user2, document_user1, document_user2):
    """❌ TEST 2.3: Utente vede solo i propri documenti nella lista."""
    response = client.get("/api/v1/documents/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Documento User1"
    
    # Verifica che non veda il documento di user2
    document_ids = [doc["id"] for doc in data]
    assert document_user2["id"] not in document_ids

# ============================================================================
# TEST 3 - Modifica Risorse per Proprietario
# ============================================================================

def test_user_can_modify_own_house(client, user1, house_user1):
    """✅ TEST 3.1: Utente può modificare la propria casa."""
    update_data = {"name": "Casa User1 Modificata"}
    response = client.put(f"/api/v1/houses/{house_user1['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Casa User1 Modificata"

def test_user_cannot_modify_other_user_house(client, user1, house_user2):
    """❌ TEST 3.2: Utente non può modificare case di altri utenti."""
    update_data = {"name": "Tentativo di Modifica"}
    response = client.put(f"/api/v1/houses/{house_user2['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_can_modify_own_document(client, user1, document_user1):
    """✅ TEST 3.3: Utente può modificare il proprio documento."""
    update_data = {"name": "Documento User1 Modificato"}
    response = client.put(f"/api/v1/documents/{document_user1['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Documento User1 Modificato"

def test_user_cannot_modify_other_user_document(client, user1, document_user2):
    """❌ TEST 3.4: Utente non può modificare documenti di altri utenti."""
    update_data = {"name": "Tentativo di Modifica"}
    response = client.put(f"/api/v1/documents/{document_user2['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 4 - Eliminazione Risorse per Proprietario
# ============================================================================

def test_user_can_delete_own_house(client, user1, house_user1):
    """✅ TEST 4.1: Utente può eliminare la propria casa."""
    response = client.delete(f"/api/v1/houses/{house_user1['id']}", headers=user1["headers"])
    assert response.status_code == 204

def test_user_cannot_delete_other_user_house(client, user1, house_user2):
    """❌ TEST 4.2: Utente non può eliminare case di altri utenti."""
    response = client.delete(f"/api/v1/houses/{house_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_can_delete_own_document(client, user1):
    """✅ TEST 4.3: Utente può eliminare il proprio documento."""
    # Prima crea una nuova casa per questo test
    house_data = {
        "name": "Casa per Eliminazione",
        "address": "Via Eliminazione 123"
    }
    house_response = client.post("/api/v1/houses/", json=house_data, headers=user1["headers"])
    assert house_response.status_code == 201
    house = house_response.json()
    
    # Crea un nuovo documento specifico per questo test
    document_data = {
        "name": "Documento da Eliminare",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/da_eliminare.pdf",
        "checksum": "abc123def456",
        "description": "Documento da eliminare",
        "house_id": house["id"]
    }
    response = client.post("/api/v1/documents/", json=document_data, headers=user1["headers"])
    assert response.status_code == 200
    document = response.json()
    
    # Ora elimina il documento appena creato
    response = client.delete(f"/api/v1/documents/{document['id']}", headers=user1["headers"])
    assert response.status_code == 200  # L'endpoint restituisce un messaggio JSON, non 204
    assert "message" in response.json()

def test_user_cannot_delete_other_user_document(client, user1, document_user2):
    """❌ TEST 4.4: Utente non può eliminare documenti di altri utenti."""
    response = client.delete(f"/api/v1/documents/{document_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 5 - Accesso Senza Autenticazione
# ============================================================================

def test_unauthenticated_access_to_houses(client, house_user1):
    """❌ TEST 5.1: Accesso non autenticato alle case è negato."""
    response = client.get("/api/v1/houses/")
    assert response.status_code == 401
    
    response = client.get(f"/api/v1/houses/{house_user1['id']}")
    assert response.status_code == 401

def test_unauthenticated_access_to_documents(client, document_user1):
    """❌ TEST 5.2: Accesso non autenticato ai documenti è negato."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 401
    
    response = client.get(f"/api/v1/documents/{document_user1['id']}")
    assert response.status_code == 401

def test_unauthenticated_modification_denied(client, house_user1, document_user1):
    """❌ TEST 5.3: Modifiche non autenticate sono negate."""
    # Tentativo di modifica casa
    response = client.put(f"/api/v1/houses/{house_user1['id']}", json={"name": "Tentativo"})
    assert response.status_code == 401
    
    # Tentativo di modifica documento
    response = client.put(f"/api/v1/documents/{document_user1['id']}", json={"name": "Tentativo"})
    assert response.status_code == 401

def test_unauthenticated_deletion_denied(client, house_user1, document_user1):
    """❌ TEST 5.4: Eliminazioni non autenticate sono negate."""
    # Tentativo di eliminazione casa
    response = client.delete(f"/api/v1/houses/{house_user1['id']}")
    assert response.status_code == 401
    
    # Tentativo di eliminazione documento
    response = client.delete(f"/api/v1/documents/{document_user1['id']}")
    assert response.status_code == 401

# ============================================================================
# TEST 6 - Creazione Risorsa
# ============================================================================

def test_user_can_create_house_for_self(client, user1):
    """✅ TEST 5.1: Utente può creare una casa per se stesso."""
    headers = user1["headers"]
    
    house_data = {
        "name": "Nuova Casa User1",
        "address": "Via Nuova 123"
    }
    
    response = client.post("/api/v1/houses/", json=house_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Nuova Casa User1"
    assert data["owner_id"] == user1["id"]

def test_user_can_create_document_for_own_house(client, user1):
    """✅ TEST 5.2: Utente può creare un documento per la propria casa."""
    headers = user1["headers"]
    
    # Prima crea una nuova casa per questo test
    house_data = {
        "name": "Casa per Documento",
        "address": "Via Documento 123"
    }
    house_response = client.post("/api/v1/houses/", json=house_data, headers=headers)
    assert house_response.status_code == 201
    house = house_response.json()
    
    # Ora crea il documento per questa casa
    document_data = {
        "name": "Nuovo Documento",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/nuovo.pdf",
        "checksum": "xyz789",
        "description": "Nuovo documento",
        "house_id": house["id"]
    }
    
    response = client.post("/api/v1/documents/", json=document_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nuovo Documento"
    assert data["owner_id"] == user1["id"]
    assert data["house_id"] == house["id"]

# ============================================================================
# TEST 7 - Accesso Cross-User Completo
# ============================================================================

def test_complete_cross_user_isolation(client, user1, user2, house_user1, house_user2, document_user1, document_user2):
    """🔒 TEST 6: Verifica completa isolamento tra utenti."""
    headers_user1 = user1["headers"]
    headers_user2 = user2["headers"]
    
    # User1 non può vedere/modificare risorse di User2
    response = client.get(f"/api/v1/houses/{house_user2['id']}", headers=headers_user1)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    response = client.put(f"/api/v1/houses/{house_user2['id']}", json={"name": "Tentativo"}, headers=headers_user1)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    response = client.delete(f"/api/v1/houses/{house_user2['id']}", headers=headers_user1)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    # User2 non può vedere/modificare risorse di User1
    response = client.get(f"/api/v1/houses/{house_user1['id']}", headers=headers_user2)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    response = client.put(f"/api/v1/houses/{house_user1['id']}", json={"name": "Tentativo"}, headers=headers_user2)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    response = client.delete(f"/api/v1/houses/{house_user1['id']}", headers=headers_user2)
    assert response.status_code in [403, 404]  # Accetta sia 403 che 404
    
    # Ogni utente può accedere solo alle proprie risorse
    response = client.get("/api/v1/houses/", headers=headers_user1)
    assert response.status_code == 200
    user1_houses = response.json()["items"]
    assert all(house["owner_id"] == user1["id"] for house in user1_houses)  # Confronta con ID invece che email
    
    response = client.get("/api/v1/houses/", headers=headers_user2)
    assert response.status_code == 200
    user2_houses = response.json()["items"]
    assert all(house["owner_id"] == user2["id"] for house in user2_houses)  # Confronta con ID invece che email

# ============================================================================
# TEST 8 - Download Documenti (TEMPORANEAMENTE COMMENTATO - Richiede MinIO)
# ============================================================================

# def test_user_can_download_own_document(client, user1, document_user1, override_minio_service):
#     """✅ TEST 7.1: Utente può scaricare i propri documenti."""
#     headers = user1["headers"]
#     
#     response = client.get(f"/api/v1/documents/download/{document_user1['id']}", headers=headers)
#     assert response.status_code == 200
#     data = response.json()
#     assert "download_url" in data

# def test_user_cannot_download_other_user_document(client, user1, document_user2, override_minio_service):
#     """❌ TEST 7.2: Utente non può scaricare documenti di altri utenti."""
#     headers = user1["headers"]
#     
#     response = client.get(f"/api/v1/documents/download/{document_user2['id']}", headers=headers)
#     assert response.status_code == 403
#     assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 9 - Upload Documenti (TEMPORANEAMENTE COMMENTATO - Richiede MinIO)
# ============================================================================

# def test_user_can_upload_to_own_document(client, user1, document_user1, override_minio_service):
#     """✅ TEST 8.1: Utente può caricare file sui propri documenti."""
#     headers = user1["headers"]
#     
#     # Simula un file di test
#     files = {"file": ("test.txt", b"test content", "text/plain")}
#     
#     response = client.post(
#         f"/api/v1/documents/{document_user1['id']}/upload",
#         files=files,
#         headers=headers
#     )
#     # Nota: questo test potrebbe fallire se MinIO non è configurato per i test
#     # Il controllo importante è che non restituisca 403
#     assert response.status_code != 403

# def test_user_cannot_upload_to_other_user_document(client, user1, document_user2, override_minio_service):
#     """❌ TEST 8.2: Utente non può caricare file su documenti di altri utenti."""
#     headers = user1["headers"]
#     
#     files = {"file": ("test.txt", b"test content", "text/plain")}
#     
#     response = client.post(
#         f"/api/v1/documents/{document_user2['id']}/upload",
#         files=files,
#         headers=headers
#     )
#     assert response.status_code == 403
#     assert "Non hai i permessi" in response.json()["detail"]

# ============================================================================
# TEST 10 - Edge Cases
# ============================================================================

def test_access_nonexistent_house(client, user1):
    """🔍 TEST 9.1: Accesso a casa inesistente."""
    headers = user1["headers"]
    
    response = client.get("/api/v1/houses/99999", headers=headers)
    assert response.status_code == 404

def test_access_nonexistent_document(client, user1):
    """🔍 TEST 9.2: Accesso a documento inesistente."""
    headers = user1["headers"]
    
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