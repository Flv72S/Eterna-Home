import requests
import json
import os
import uuid
import io
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "integration_test@example.com"
TEST_PASSWORD = "testpassword"
TEST_HOUSE_NAME = "Casa di Test"
TEST_NODE_LOCATION = "Posizione di Test"
TEST_NODE_TYPE = "Tipo di Test"

@dataclass
class TestResult:
    """Classe per memorizzare i risultati dei test"""
    name: str
    success: bool
    message: str
    timestamp: datetime = datetime.now()

class TestResources:
    """Classe per tracciare e pulire le risorse di test"""
    def __init__(self):
        self.house_id: Optional[int] = None
        self.node_id: Optional[int] = None
        self.document_id: Optional[int] = None
        self.temp_files: list[str] = []

    def cleanup(self, access_token: str) -> None:
        """Pulisce tutte le risorse di test"""
        headers = get_headers(access_token)
        
        # Pulisce il documento se esiste
        if self.document_id:
            try:
                requests.delete(f"{BASE_URL}/legacy-documents/{self.document_id}", headers=headers)
            except Exception as e:
                print(f"Attenzione: Impossibile eliminare il documento {self.document_id}: {e}")

        # Pulisce il nodo se esiste
        if self.node_id:
            try:
                requests.delete(f"{BASE_URL}/nodes/{self.node_id}", headers=headers)
            except Exception as e:
                print(f"Attenzione: Impossibile eliminare il nodo {self.node_id}: {e}")

        # Pulisce la casa se esiste
        if self.house_id:
            try:
                requests.delete(f"{BASE_URL}/houses/{self.house_id}", headers=headers)
            except Exception as e:
                print(f"Attenzione: Impossibile eliminare la casa {self.house_id}: {e}")

        # Pulisce i file temporanei
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Attenzione: Impossibile eliminare il file temporaneo {file_path}: {e}")

def print_test_result(result: TestResult) -> None:
    """Stampa il risultato del test in modo formattato"""
    status = "SUCCESSO" if result.success else "FALLITO"
    print(f"\nTest {result.name}: {status}")
    print(f"Orario: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    if result.message:
        print(f"Messaggio: {result.message}")
    print("-" * 50)

def get_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """Ottiene gli header con autorizzazione opzionale"""
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

def test_signup() -> TestResult:
    """Test di registrazione utente"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers=get_headers()
        )
        
        if response.status_code in [200, 400]:  # 400 se l'utente esiste già
            return TestResult(
                "Registrazione",
                True,
                "Utente creato" if response.status_code == 200 else "Utente già esistente"
            )
        else:
            return TestResult(
                "Registrazione",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Registrazione", False, str(e))

def test_login() -> Tuple[TestResult, Optional[str]]:
    """Test di login utente e ottenimento token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            return TestResult("Login", True, "Token di accesso ottenuto con successo"), access_token
        else:
            return TestResult("Login", False, f"Codice di stato inatteso: {response.status_code}"), None
    except Exception as e:
        return TestResult("Login", False, str(e)), None

def test_create_house(access_token: str, resources: TestResources) -> TestResult:
    """Test di creazione casa e restituzione ID"""
    try:
        response = requests.post(
            f"{BASE_URL}/houses/",
            json={"name": TEST_HOUSE_NAME},
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            resources.house_id = response.json()["id"]
            return TestResult("Creazione Casa", True, f"Casa creata con ID: {resources.house_id}")
        else:
            return TestResult("Creazione Casa", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Creazione Casa", False, str(e))

def test_create_node(access_token: str, resources: TestResources) -> TestResult:
    """Test di creazione nodo e restituzione ID"""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/",
            json={
                "house_id": resources.house_id,
                "location": TEST_NODE_LOCATION,
                "type": TEST_NODE_TYPE
            },
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            resources.node_id = response.json()["id"]
            return TestResult("Creazione Nodo", True, f"Nodo creato con ID: {resources.node_id}")
        else:
            return TestResult("Creazione Nodo", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Creazione Nodo", False, str(e))

def test_protected_endpoint(access_token: str) -> TestResult:
    """Test di accesso all'endpoint protetto"""
    try:
        response = requests.get(
            f"{BASE_URL}/maintenance/test-maintenance",
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            return TestResult("Endpoint Protetto", True, "Accesso all'endpoint protetto riuscito")
        else:
            return TestResult("Endpoint Protetto", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Endpoint Protetto", False, str(e))

def test_upload_legacy_document(access_token: str, resources: TestResources) -> TestResult:
    """Test di caricamento documento legacy e restituzione ID"""
    try:
        # Crea file di test temporaneo
        temp_file_path = f"temp_test_document_{uuid.uuid4()}.txt"
        resources.temp_files.append(temp_file_path)
        
        with open(temp_file_path, "w") as f:
            f.write("Questo è il contenuto del documento di test")
        
        # Prepara i dati del form multipart
        files = {
            'file': ('temp_test_document.txt', open(temp_file_path, 'rb'), 'text/plain')
        }
        data = {
            'house_id': str(resources.house_id),
            'node_id': str(resources.node_id),
            'type': 'TXT',
            'version': '1.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/legacy-documents",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            resources.document_id = response.json()["id"]
            return TestResult(
                "Caricamento Documento Legacy",
                True,
                f"Documento caricato con successo con ID: {resources.document_id}"
            )
        else:
            return TestResult(
                "Caricamento Documento Legacy",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Caricamento Documento Legacy", False, str(e))

def test_get_legacy_documents(access_token: str, resources: TestResources) -> TestResult:
    """Test di recupero documenti legacy"""
    try:
        response = requests.get(
            f"{BASE_URL}/legacy-documents/{resources.node_id}",
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            documents = response.json()
            success = len(documents) > 0
            return TestResult(
                "Recupero Documenti Legacy",
                success,
                f"Trovati {len(documents)} documenti" if success else "Nessun documento trovato"
            )
        else:
            return TestResult(
                "Recupero Documenti Legacy",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Recupero Documenti Legacy", False, str(e))

def main():
    """Funzione principale di esecuzione dei test"""
    print("Avvio Test di Integrazione...")
    print("=" * 50)
    
    resources = TestResources()
    test_results: list[TestResult] = []
    
    try:
        # Test di registrazione
        signup_result = test_signup()
        print_test_result(signup_result)
        test_results.append(signup_result)
        if not signup_result.success:
            print("Registrazione fallita, interruzione dei test")
            return
        
        # Test di login
        login_result, access_token = test_login()
        print_test_result(login_result)
        test_results.append(login_result)
        if not login_result.success:
            print("Login fallito, interruzione dei test")
            return
        
        # Test di creazione casa
        house_result = test_create_house(access_token, resources)
        print_test_result(house_result)
        test_results.append(house_result)
        if not house_result.success:
            print("Creazione casa fallita, interruzione dei test")
            return
        
        # Test di creazione nodo
        node_result = test_create_node(access_token, resources)
        print_test_result(node_result)
        test_results.append(node_result)
        if not node_result.success:
            print("Creazione nodo fallita, interruzione dei test")
            return
        
        # Test endpoint protetto
        protected_result = test_protected_endpoint(access_token)
        print_test_result(protected_result)
        test_results.append(protected_result)
        
        # Test caricamento documento legacy
        upload_result = test_upload_legacy_document(access_token, resources)
        print_test_result(upload_result)
        test_results.append(upload_result)
        if not upload_result.success:
            print("Caricamento documento fallito, interruzione dei test")
            return
        
        # Test recupero documenti legacy
        get_docs_result = test_get_legacy_documents(access_token, resources)
        print_test_result(get_docs_result)
        test_results.append(get_docs_result)
        
        # Stampa riepilogo
        print("\nRiepilogo Test:")
        print("=" * 50)
        success_count = sum(1 for r in test_results if r.success)
        print(f"Totale Test: {len(test_results)}")
        print(f"Test Riusciti: {success_count}")
        print(f"Test Falliti: {len(test_results) - success_count}")
        print("=" * 50)
        
    finally:
        # Pulizia risorse
        if 'access_token' in locals():
            print("\nPulizia risorse di test...")
            resources.cleanup(access_token)
            print("Pulizia completata")
    
    print("\nTest di Integrazione Completati!")
    print("=" * 50)

if __name__ == "__main__":
    main() 