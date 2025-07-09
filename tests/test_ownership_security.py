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
from app.core.security import create_access_token
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

def create_test_user_via_api(client, user_id: int):
    """Crea un utente di test tramite API."""
    data = {
        "email": f"testuser{user_id}@example.com",
        "username": f"testuser{user_id}",
        "password": "testpassword123",
        "full_name": f"Test User {user_id}"
    }
    response = client.post("/api/v1/auth/register", json=data)
    assert response.status_code in (200, 201), f"Registration failed: {response.text}"
    return response.json()

def create_test_house_via_api(client, user, house_name):
    """Crea una casa di test tramite API."""
    house_data = {
        "name": house_name,
        "address": f"Via {house_name}",
        "description": f"Casa di {house_name}"
    }
    response = client.post("/api/v1/houses/", json=house_data, headers=user["headers"])
    assert response.status_code in (200, 201), f"House creation failed: {response.text}"
    return response.json()

def create_test_document_via_api(client, user, house_id, document_name):
    """Crea un documento di test tramite API."""
    document_data = {
        "name": document_name,
        "type": "application/pdf",
        "size": 1024,
        "path": f"/documents/{document_name.lower().replace(' ', '_')}.pdf",
        "checksum": f"checksum_{document_name.lower().replace(' ', '_')}",
        "description": f"Documento {document_name}",
        "house_id": house_id
    }
    response = client.post("/api/v1/documents/", json=document_data, headers=user["headers"])
    assert response.status_code in (200, 201), f"Document creation failed: {response.text}"
    return response.json()

# ============================================================================
# TEST 1 - Accesso Case per Proprietario
# ============================================================================

def test_user_can_access_own_houses(client):
    """✅ TEST 1.1: Utente può visualizzare le proprie case."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    
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

def test_user_cannot_access_other_user_houses(client):
    """❌ TEST 1.2: Utente non può accedere a case di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    
    # Tentativo di accesso a casa di user2
    response = client.get(f"/api/v1/houses/{house_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_houses_in_list(client):
    """❌ TEST 1.3: Utente vede solo le proprie case nella lista."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    
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

def test_user_can_access_own_documents(client):
    """✅ TEST 2.1: Utente può visualizzare i propri documenti."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    # Lista documenti
    response = client.get("/api/v1/documents/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Documento User1"
    
    # Dettaglio documento
    response = client.get(f"/api/v1/documents/{document_user1['id']}", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Documento User1"

def test_user_cannot_access_other_user_documents(client):
    """❌ TEST 2.2: Utente non può accedere a documenti di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    document_user2 = create_test_document_via_api(client, user2, house_user2["id"], "Documento User2")
    
    # Tentativo di accesso a documento di user2
    response = client.get(f"/api/v1/documents/{document_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    assert "Non hai i permessi" in response.json()["detail"]

def test_user_cannot_see_other_user_documents_in_list(client):
    """❌ TEST 2.3: Utente vede solo i propri documenti nella lista."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    document_user2 = create_test_document_via_api(client, user2, house_user2["id"], "Documento User2")
    
    response = client.get("/api/v1/documents/", headers=user1["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Documento User1"
    
    # Verifica che non veda il documento di user2
    document_ids = [doc["id"] for doc in data["items"]]
    assert document_user2["id"] not in document_ids

# ============================================================================
# TEST 3 - Modifica Risorse per Proprietario
# ============================================================================

def test_user_can_modify_own_house(client):
    """✅ TEST 3.1: Utente può modificare la propria casa."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    
    update_data = {"name": "Casa User1 Modificata"}
    response = client.put(f"/api/v1/houses/{house_user1['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 200

def test_user_cannot_modify_other_user_house(client):
    """❌ TEST 3.2: Utente non può modificare case di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    
    update_data = {"name": "Casa User2 Modificata"}
    response = client.put(f"/api/v1/houses/{house_user2['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 403

def test_user_can_modify_own_document(client):
    """✅ TEST 3.3: Utente può modificare il proprio documento."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    update_data = {"name": "Documento User1 Modificato"}
    response = client.put(f"/api/v1/documents/{document_user1['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 200

def test_user_cannot_modify_other_user_document(client):
    """❌ TEST 3.4: Utente non può modificare documenti di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    document_user2 = create_test_document_via_api(client, user2, house_user2["id"], "Documento User2")
    
    update_data = {"name": "Documento User2 Modificato"}
    response = client.put(f"/api/v1/documents/{document_user2['id']}", json=update_data, headers=user1["headers"])
    assert response.status_code == 403

# ============================================================================
# TEST 4 - Eliminazione Risorse per Proprietario
# ============================================================================

def test_user_can_delete_own_house(client):
    """✅ TEST 4.1: Utente può eliminare la propria casa."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    
    response = client.delete(f"/api/v1/houses/{house_user1['id']}", headers=user1["headers"])
    assert response.status_code == 200

def test_user_cannot_delete_other_user_house(client):
    """❌ TEST 4.2: Utente non può eliminare case di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    
    response = client.delete(f"/api/v1/houses/{house_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403

def test_user_can_delete_own_document(client):
    """✅ TEST 4.3: Utente può eliminare il proprio documento."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    response = client.delete(f"/api/v1/documents/{document_user1['id']}", headers=user1["headers"])
    assert response.status_code == 200

def test_user_cannot_delete_other_user_document(client):
    """❌ TEST 4.4: Utente non può eliminare documenti di altri utenti."""
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    document_user2 = create_test_document_via_api(client, user2, house_user2["id"], "Documento User2")
    
    response = client.delete(f"/api/v1/documents/{document_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403

# ============================================================================
# TEST 5 - Accesso Non Autenticato
# ============================================================================

def test_unauthenticated_access_to_houses(client):
    """❌ TEST 5.1: Accesso non autenticato a case negato."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    
    response = client.get(f"/api/v1/houses/{house_user1['id']}")
    assert response.status_code == 401

def test_unauthenticated_access_to_documents(client):
    """❌ TEST 5.2: Accesso non autenticato a documenti negato."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    response = client.get(f"/api/v1/documents/{document_user1['id']}")
    assert response.status_code == 401

def test_unauthenticated_modification_denied(client):
    """❌ TEST 5.3: Modifica non autenticata negata."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    # Tentativo di modifica casa
    response = client.put(f"/api/v1/houses/{house_user1['id']}", json={"name": "Modificata"})
    assert response.status_code == 401
    
    # Tentativo di modifica documento
    response = client.put(f"/api/v1/documents/{document_user1['id']}", json={"name": "Modificato"})
    assert response.status_code == 401

def test_unauthenticated_deletion_denied(client):
    """❌ TEST 5.4: Eliminazione non autenticata negata."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    
    # Tentativo di eliminazione casa
    response = client.delete(f"/api/v1/houses/{house_user1['id']}")
    assert response.status_code == 401
    
    # Tentativo di eliminazione documento
    response = client.delete(f"/api/v1/documents/{document_user1['id']}")
    assert response.status_code == 401

# ============================================================================
# TEST 6 - Creazione Risorse
# ============================================================================

def test_user_can_create_house_for_self(client):
    """✅ TEST 6.1: Utente può creare casa per se stesso."""
    user1 = create_test_user_via_api(client, 1)
    
    house_data = {
        "name": "Nuova Casa",
        "address": "Via Nuova 123",
        "description": "Casa appena creata"
    }
    response = client.post("/api/v1/houses/", json=house_data, headers=user1["headers"])
    assert response.status_code in (200, 201)
    
    # Verifica che la casa appartenga all'utente
    house_id = response.json()["id"]
    get_response = client.get(f"/api/v1/houses/{house_id}", headers=user1["headers"])
    assert get_response.status_code == 200

def test_user_can_create_document_for_own_house(client):
    """✅ TEST 6.2: Utente può creare documento per la propria casa."""
    user1 = create_test_user_via_api(client, 1)
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    
    document_data = {
        "name": "Nuovo Documento",
        "type": "application/pdf",
        "size": 1024,
        "path": "/documents/nuovo_documento.pdf",
        "checksum": "checksum_nuovo",
        "description": "Documento appena creato",
        "house_id": house_user1["id"]
    }
    response = client.post("/api/v1/documents/", json=document_data, headers=user1["headers"])
    assert response.status_code in (200, 201)
    
    # Verifica che il documento appartenga all'utente
    document_id = response.json()["id"]
    get_response = client.get(f"/api/v1/documents/{document_id}", headers=user1["headers"])
    assert get_response.status_code == 200

# ============================================================================
# TEST 7 - Isolamento Completo tra Utenti
# ============================================================================

def test_complete_cross_user_isolation(client):
    """✅ TEST 7: Isolamento completo tra utenti."""
    # Crea due utenti con le loro risorse
    user1 = create_test_user_via_api(client, 1)
    user2 = create_test_user_via_api(client, 2)
    
    house_user1 = create_test_house_via_api(client, user1, "Casa User1")
    house_user2 = create_test_house_via_api(client, user2, "Casa User2")
    
    document_user1 = create_test_document_via_api(client, user1, house_user1["id"], "Documento User1")
    document_user2 = create_test_document_via_api(client, user2, house_user2["id"], "Documento User2")
    
    # User1 non può accedere a risorse di User2
    response = client.get(f"/api/v1/houses/{house_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    
    response = client.get(f"/api/v1/documents/{document_user2['id']}", headers=user1["headers"])
    assert response.status_code == 403
    
    # User2 non può accedere a risorse di User1
    response = client.get(f"/api/v1/houses/{house_user1['id']}", headers=user2["headers"])
    assert response.status_code == 403
    
    response = client.get(f"/api/v1/documents/{document_user1['id']}", headers=user2["headers"])
    assert response.status_code == 403
    
    # Ogni utente vede solo le proprie risorse nelle liste
    response = client.get("/api/v1/houses/", headers=user1["headers"])
    assert response.status_code == 200
    user1_houses = response.json()["items"]
    assert len(user1_houses) == 1
    assert user1_houses[0]["id"] == house_user1["id"]
    
    response = client.get("/api/v1/houses/", headers=user2["headers"])
    assert response.status_code == 200
    user2_houses = response.json()["items"]
    assert len(user2_houses) == 1
    assert user2_houses[0]["id"] == house_user2["id"]
    
    response = client.get("/api/v1/documents/", headers=user1["headers"])
    assert response.status_code == 200
    user1_documents = response.json()["items"]
    assert len(user1_documents) == 1
    assert user1_documents[0]["id"] == document_user1["id"]
    
    response = client.get("/api/v1/documents/", headers=user2["headers"])
    assert response.status_code == 200
    user2_documents = response.json()["items"]
    assert len(user2_documents) == 1
    assert user2_documents[0]["id"] == document_user2["id"]

# ============================================================================
# TEST 8 - Casi Edge
# ============================================================================

def test_access_nonexistent_house(client):
    """❌ TEST 8.1: Accesso a casa inesistente."""
    user1 = create_test_user_via_api(client, 1)
    
    response = client.get("/api/v1/houses/999999", headers=user1["headers"])
    assert response.status_code == 404

def test_access_nonexistent_document(client):
    """❌ TEST 8.2: Accesso a documento inesistente."""
    user1 = create_test_user_via_api(client, 1)
    
    response = client.get("/api/v1/documents/999999", headers=user1["headers"])
    assert response.status_code == 404

def test_unauthorized_access_without_token(client):
    """❌ TEST 8.3: Accesso senza token."""
    response = client.get("/api/v1/houses/")
    assert response.status_code == 401
    
    response = client.get("/api/v1/documents/")
    assert response.status_code == 401

def test_unauthorized_access_with_invalid_token(client):
    """❌ TEST 8.4: Accesso con token non valido."""
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = client.get("/api/v1/houses/", headers=headers)
    assert response.status_code == 401
    
    response = client.get("/api/v1/documents/", headers=headers)
    assert response.status_code == 401 