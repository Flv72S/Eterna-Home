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
test_house_id = None
test_node_id = None
test_legacy_document_id = None

def test_register_user():
    """Test registrazione utente"""
    global test_token
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    test_token = data["access_token"]
    print(f"✅ Test registrazione utente completato. Token: {test_token[:10]}...")

def test_login():
    """Test login utente"""
    global test_token
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    test_token = data["access_token"]
    print(f"✅ Test login completato. Token: {test_token[:10]}...")

def test_create_house():
    """Test creazione casa"""
    global test_house_id
    headers = {"Authorization": f"Bearer {test_token}"}
    response = requests.post(f"{BASE_URL}/houses/", json=TEST_HOUSE, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    test_house_id = data["id"]
    print(f"✅ Test creazione casa completato. ID: {test_house_id}")

def test_create_node():
    """Test creazione nodo"""
    global test_node_id
    headers = {"Authorization": f"Bearer {test_token}"}
    node_data = {**TEST_NODE, "house_id": test_house_id}
    response = requests.post(f"{BASE_URL}/nodes/", json=node_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    test_node_id = data["id"]
    print(f"✅ Test creazione nodo completato. ID: {test_node_id}")

def test_upload_legacy_document():
    """Test upload documento legacy"""
    global test_legacy_document_id
    headers = {"Authorization": f"Bearer {test_token}"}
    
    # Crea un file di test
    test_file_path = "test_document.txt"
    with open(test_file_path, "w") as f:
        f.write("Test document content")
    
    # Prepara i dati per l'upload
    files = {
        "file": ("test_document.txt", open(test_file_path, "rb"), "text/plain")
    }
    data = {
        "node_id": test_node_id,
        "document_type": "manual",
        "description": "Test document"
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
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "file_url" in data
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
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(doc["id"] == test_legacy_document_id for doc in data)
    print(f"✅ Test recupero documenti legacy completato. Trovati {len(data)} documenti")

def run_all_tests():
    """Esegue tutti i test in sequenza"""
    print("🚀 Inizio test di integrazione...")
    
    try:
        test_register_user()
        test_login()
        test_create_house()
        test_create_node()
        test_upload_legacy_document()
        test_get_legacy_documents()
        print("✨ Tutti i test completati con successo!")
    except AssertionError as e:
        print(f"❌ Test fallito: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione dei test: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_tests() 