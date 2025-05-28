import requests
import json
import os
from datetime import datetime
import pytest
from typing import Dict, Any

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
    "password": "testpassword123"
}
TEST_ADMIN = {
    "email": f"admin_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
    "password": "adminpassword123",
    "role": "admin"
}
TEST_HOUSE = {
    "name": "Test House",
    "address": "123 Test Street",
    "city": "Test City"
}
TEST_NODE = {
    "name": "Test Node",
    "type": "sensor",
    "location": "Living Room"
}

# Variabili globali per i test
test_token = None
test_admin_token = None
test_house_id = None
test_node_id = None
test_legacy_document_id = None

def test_register_user():
    """Test registrazione utente"""
    global test_token
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    assert response.status_code == 200, f"Registrazione fallita con status code {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Token di accesso non presente nella risposta"
    assert len(data["access_token"]) > 0, "Token di accesso vuoto"
    test_token = data["access_token"]
    print(f"✅ Test registrazione utente completato. Token: {test_token[:10]}...")

def test_register_admin():
    """Test registrazione utente admin"""
    global test_admin_token
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_ADMIN)
    assert response.status_code == 200, f"Registrazione admin fallita con status code {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Token di accesso non presente nella risposta"
    assert len(data["access_token"]) > 0, "Token di accesso vuoto"
    test_admin_token = data["access_token"]
    print(f"✅ Test registrazione admin completato. Token: {test_admin_token[:10]}...")

def test_login():
    """Test login utente"""
    global test_token
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    assert response.status_code == 200, f"Login fallito con status code {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Token di accesso non presente nella risposta"
    assert len(data["access_token"]) > 0, "Token di accesso vuoto"
    test_token = data["access_token"]
    print(f"✅ Test login completato. Token: {test_token[:10]}...")

def test_admin_login():
    """Test login admin"""
    global test_admin_token
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_ADMIN)
    assert response.status_code == 200, f"Login admin fallito con status code {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Token di accesso non presente nella risposta"
    assert len(data["access_token"]) > 0, "Token di accesso vuoto"
    test_admin_token = data["access_token"]
    print(f"✅ Test login admin completato. Token: {test_admin_token[:10]}...")

def test_create_house():
    """Test creazione casa"""
    global test_house_id
    headers = {"Authorization": f"Bearer {test_token}"}
    response = requests.post(f"{BASE_URL}/houses/", json=TEST_HOUSE, headers=headers)
    assert response.status_code == 200, f"Creazione casa fallita con status code {response.status_code}"
    data = response.json()
    assert "id" in data, "ID casa non presente nella risposta"
    assert len(data["id"]) > 0, "ID casa vuoto"
    assert data["name"] == TEST_HOUSE["name"], "Nome casa non corrisponde"
    assert data["address"] == TEST_HOUSE["address"], "Indirizzo casa non corrisponde"
    assert data["city"] == TEST_HOUSE["city"], "Città casa non corrisponde"
    test_house_id = data["id"]
    print(f"✅ Test creazione casa completato. ID: {test_house_id}")

def test_create_node():
    """Test creazione nodo"""
    global test_node_id
    headers = {"Authorization": f"Bearer {test_token}"}
    node_data = {**TEST_NODE, "house_id": test_house_id}
    response = requests.post(f"{BASE_URL}/nodes/", json=node_data, headers=headers)
    assert response.status_code == 200, f"Creazione nodo fallita con status code {response.status_code}"
    data = response.json()
    assert "id" in data, "ID nodo non presente nella risposta"
    assert len(data["id"]) > 0, "ID nodo vuoto"
    assert data["name"] == TEST_NODE["name"], "Nome nodo non corrisponde"
    assert data["type"] == TEST_NODE["type"], "Tipo nodo non corrisponde"
    assert data["location"] == TEST_NODE["location"], "Posizione nodo non corrisponde"
    assert data["house_id"] == test_house_id, "ID casa non corrisponde"
    test_node_id = data["id"]
    print(f"✅ Test creazione nodo completato. ID: {test_node_id}")

def test_upload_legacy_document():
    """Test upload documento legacy"""
    global test_legacy_document_id
    headers = {"Authorization": f"Bearer {test_token}"}
    
    # Crea un file di test
    test_file_path = "test_document.txt"
    test_content = "Test document content"
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    # Prepara i dati per l'upload
    files = {
        "file": ("test_document.txt", open(test_file_path, "rb"), "text/plain")
    }
    data = {
        "node_id": test_node_id,
        "document_type": "manual"
    }
    
    # Esegui l'upload
    response = requests.post(
        f"{BASE_URL}/legacy-documents/",
        files=files,
        data=data,
        headers=headers
    )
    
    # Pulisci il file di test
    os.remove(test_file_path)
    
    # Verifica la risposta
    assert response.status_code == 200, f"Upload documento fallito con status code {response.status_code}"
    data = response.json()
    assert "id" in data, "ID documento non presente nella risposta"
    assert len(data["id"]) > 0, "ID documento vuoto"
    assert "file_url" in data, "URL file non presente nella risposta"
    assert len(data["file_url"]) > 0, "URL file vuoto"
    assert data["node_id"] == test_node_id, "ID nodo non corrisponde"
    assert data["document_type"] == "manual", "Tipo documento non corrisponde"
    test_legacy_document_id = data["id"]
    print(f"✅ Test upload documento legacy completato. ID: {test_legacy_document_id}")
    print(f"   File URL: {data['file_url']}")

def test_get_legacy_documents():
    """Test recupero documenti legacy"""
    headers = {"Authorization": f"Bearer {test_token}"}
    response = requests.get(
        f"{BASE_URL}/legacy-documents/{test_node_id}",
        headers=headers
    )
    assert response.status_code == 200, f"Recupero documenti fallito con status code {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "La risposta non è una lista"
    assert len(data) > 0, "Nessun documento trovato"
    
    # Verifica che il documento caricato sia presente
    found_document = False
    for doc in data:
        if doc["id"] == test_legacy_document_id:
            found_document = True
            assert doc["node_id"] == test_node_id, "ID nodo non corrisponde"
            assert doc["document_type"] == "manual", "Tipo documento non corrisponde"
            assert "file_url" in doc, "URL file non presente"
            assert len(doc["file_url"]) > 0, "URL file vuoto"
            break
    
    assert found_document, f"Documento con ID {test_legacy_document_id} non trovato nella lista"
    print(f"✅ Test recupero documenti legacy completato. Trovati {len(data)} documenti")

def test_admin_access_allowed():
    """Test accesso consentito per admin"""
    headers = {"Authorization": f"Bearer {test_admin_token}"}
    response = requests.get(f"{BASE_URL}/admin-only", headers=headers)
    assert response.status_code == 200, f"Accesso admin fallito con status code {response.status_code}"
    data = response.json()
    assert "message" in data, "Messaggio non presente nella risposta"
    assert data["message"] == "Hello admin", "Messaggio non corrisponde"
    print("✅ Test accesso admin completato con successo")

def test_admin_access_denied():
    """Test accesso negato per utente non admin"""
    headers = {"Authorization": f"Bearer {test_token}"}
    response = requests.get(f"{BASE_URL}/admin-only", headers=headers)
    assert response.status_code == 403, f"Accesso non admin non bloccato con status code {response.status_code}"
    data = response.json()
    assert "detail" in data, "Dettaglio errore non presente nella risposta"
    assert data["detail"] == "Not enough permissions", "Messaggio di errore non corrisponde"
    print("✅ Test accesso negato completato con successo")

def run_all_tests():
    """Esegue tutti i test in sequenza"""
    print("🚀 Inizio test di integrazione...")
    
    try:
        test_register_user()
        test_register_admin()
        test_login()
        test_admin_login()
        test_create_house()
        test_create_node()
        test_upload_legacy_document()
        test_get_legacy_documents()
        test_admin_access_allowed()
        test_admin_access_denied()
        print("✨ Tutti i test completati con successo!")
    except AssertionError as e:
        print(f"❌ Test fallito: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione dei test: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_tests() 