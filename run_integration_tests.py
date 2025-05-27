import requests
import json
import os
import uuid
import io
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import logging
from fastapi import status

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "new_test_user@example.com"
TEST_PASSWORD = "newsecurepassword123"
TEST_HOUSE_NAME = "Casa di Test"
TEST_HOUSE_ADDRESS = "Via Roma 123, Milano"
TEST_NODE_NAME = "Nodo di Test"
TEST_NODE_LOCATION = "Posizione di Test"
TEST_NODE_TYPE = "Tipo di Test"
TEMP_FILE_NAME = "temp_test_document.txt"

# Definizione credenziali amministratore
ADMIN_TEST_EMAIL = "admin_test@example.com"
ADMIN_TEST_PASSWORD = "adminsecurepassword"

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
        self.temp_files: List[str] = []

    def cleanup(self, access_token: str) -> None:
        """Pulisce tutte le risorse di test"""
        headers = get_headers(access_token)
        
        # Pulisce il documento se esiste
        if self.document_id:
            try:
                requests.delete(f"{BASE_URL}/legacy-documents/{self.document_id}", headers=headers)
            except Exception as e:
                logger.error(f"Attenzione: Impossibile eliminare il documento {self.document_id}: {e}")

        # Pulisce il nodo se esiste
        if self.node_id:
            try:
                requests.delete(f"{BASE_URL}/nodes/{self.node_id}", headers=headers)
            except Exception as e:
                logger.error(f"Attenzione: Impossibile eliminare il nodo {self.node_id}: {e}")

        # Pulisce la casa se esiste
        if self.house_id:
            try:
                requests.delete(f"{BASE_URL}/houses/{self.house_id}", headers=headers)
            except Exception as e:
                logger.error(f"Attenzione: Impossibile eliminare la casa {self.house_id}: {e}")

        # Pulisce i file temporanei
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Attenzione: Impossibile eliminare il file temporaneo {file_path}: {e}")

def print_test_result(result: TestResult) -> None:
    """Stampa il risultato del test in modo formattato"""
    status = "SUCCESSO" if result.success else "FALLITO"
    logger.info(f"\nTest {result.name}: {status}")
    logger.info(f"Orario: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    if result.message:
        logger.info(f"Messaggio: {result.message}")
    logger.info("-" * 50)

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
            json={
                "name": TEST_HOUSE_NAME,
                "address": TEST_HOUSE_ADDRESS
            },
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            response_data = response.json()
            house_id = response_data.get("id")
            
            # Verifica che l'ID non sia vuoto
            if not house_id:
                return TestResult("Creazione Casa", False, "ID casa non presente nella risposta")
            
            # Verifica che i dati restituiti corrispondano a quelli inviati
            if response_data.get("name") != TEST_HOUSE_NAME or response_data.get("address") != TEST_HOUSE_ADDRESS:
                return TestResult("Creazione Casa", False, "Dati casa non corrispondenti")
            
            resources.house_id = house_id
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
                "name": TEST_NODE_NAME,
                "house_id": resources.house_id,
                "location": TEST_NODE_LOCATION,
                "type": TEST_NODE_TYPE
            },
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            response_data = response.json()
            node_id = response_data.get("id")
            
            # Verifica che l'ID non sia vuoto
            if not node_id:
                return TestResult("Creazione Nodo", False, "ID nodo non presente nella risposta")
            
            # Verifica che i dati restituiti corrispondano a quelli inviati
            if (response_data.get("name") != TEST_NODE_NAME or 
                response_data.get("house_id") != resources.house_id or
                response_data.get("location") != TEST_NODE_LOCATION or
                response_data.get("type") != TEST_NODE_TYPE):
                return TestResult("Creazione Nodo", False, "Dati nodo non corrispondenti")
            
            resources.node_id = node_id
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
            'version': '1.0',
            'description': 'Documento di test'
        }
        
        response = requests.post(
            f"{BASE_URL}/legacy-documents/",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            document_id = response_data.get("id")
            file_url = response_data.get("file_url")
            
            # Verifica che l'ID e l'URL del file non siano vuoti
            if not document_id:
                return TestResult("Caricamento Documento Legacy", False, "ID documento non presente nella risposta")
            if not file_url:
                return TestResult("Caricamento Documento Legacy", False, "URL file non presente nella risposta")
            
            # Verifica che i dati restituiti corrispondano a quelli inviati
            if (response_data.get("house_id") != resources.house_id or
                response_data.get("node_id") != resources.node_id or
                response_data.get("type") != 'TXT' or
                response_data.get("version") != '1.0' or
                response_data.get("description") != 'Documento di test'):
                return TestResult("Caricamento Documento Legacy", False, "Dati documento non corrispondenti")
            
            resources.document_id = document_id
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
            
            # Verifica che la risposta sia una lista
            if not isinstance(documents, list):
                return TestResult("Recupero Documenti Legacy", False, "La risposta non è una lista")
            
            # Verifica che ci sia almeno un documento
            if len(documents) == 0:
                return TestResult("Recupero Documenti Legacy", False, "Nessun documento trovato")
            
            # Cerca il documento appena caricato
            found_document = None
            for doc in documents:
                if doc.get("id") == resources.document_id:
                    found_document = doc
                    break
            
            if not found_document:
                return TestResult("Recupero Documenti Legacy", False, "Documento caricato non trovato nella lista")
            
            # Verifica che il documento trovato abbia tutti i campi necessari
            required_fields = ["id", "file_url", "type", "version", "description"]
            missing_fields = [field for field in required_fields if field not in found_document]
            if missing_fields:
                return TestResult(
                    "Recupero Documenti Legacy",
                    False,
                    f"Campi mancanti nel documento: {', '.join(missing_fields)}"
                )
            
            return TestResult(
                "Recupero Documenti Legacy",
                True,
                f"Trovati {len(documents)} documenti, incluso il documento caricato"
            )
        else:
            return TestResult(
                "Recupero Documenti Legacy",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Recupero Documenti Legacy", False, str(e))

def test_register_admin_user():
    """Test per la registrazione di un utente amministratore"""
    logger.info("Avvio Test Registrazione Utente Amministratore...")
    logger.info("=" * 50)

    try:
        # Registrazione utente amministratore
        logger.info("\nRegistrazione utente amministratore...")
        signup_data = {
            "email": ADMIN_TEST_EMAIL,
            "full_name": "Admin Test User",
            "password": ADMIN_TEST_PASSWORD,
            "role": "admin"
        }
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        logger.info(f"Codice di stato ricevuto: {response.status_code}")
        logger.info(f"Risposta completa: {response.text}")

        if response.status_code == 200:
            logger.info("Utente amministratore registrato con successo")
            return True
        elif response.status_code in [400, 409]:
            logger.info("Utente amministratore già registrato")
            return True
        else:
            logger.error("Registrazione utente amministratore fallita")
            return False

    except Exception as e:
        logger.error(f"Errore durante il test: {str(e)}")
        return False

def test_admin_access_denied(access_token: str) -> TestResult:
    """Test che verifica che un utente 'user' non possa accedere all'endpoint admin-only"""
    try:
        response = requests.get(
            f"{BASE_URL}/users/admin-only",
            headers=get_headers(access_token)
        )
        if response.status_code == status.HTTP_403_FORBIDDEN:
            expected = {"detail": "Not enough permissions"}
            if response.json() == expected:
                return TestResult(
                    "Accesso Negato Endpoint Admin",
                    True,
                    "Accesso negato come previsto con 403 e messaggio corretto"
                )
            else:
                return TestResult(
                    "Accesso Negato Endpoint Admin",
                    False,
                    f"Messaggio di errore inatteso: {response.json()}"
                )
        else:
            return TestResult(
                "Accesso Negato Endpoint Admin",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Accesso Negato Endpoint Admin", False, str(e))

def main():
    """Funzione principale di esecuzione dei test"""
    logger.info("Avvio Test di Integrazione...")
    logger.info("=" * 50)
    
    resources = TestResources()
    test_results: List[TestResult] = []
    
    try:
        # Test di registrazione
        signup_result = test_signup()
        print_test_result(signup_result)
        test_results.append(signup_result)
        if not signup_result.success:
            logger.error("Registrazione fallita, interruzione dei test")
            return
        
        # Test di login
        login_result, access_token = test_login()
        print_test_result(login_result)
        test_results.append(login_result)
        if not login_result.success:
            logger.error("Login fallito, interruzione dei test")
            return
        
        # Test di creazione casa
        house_result = test_create_house(access_token, resources)
        print_test_result(house_result)
        test_results.append(house_result)
        if not house_result.success:
            logger.error("Creazione casa fallita, interruzione dei test")
            return
        
        # Test di creazione nodo
        node_result = test_create_node(access_token, resources)
        print_test_result(node_result)
        test_results.append(node_result)
        if not node_result.success:
            logger.error("Creazione nodo fallita, interruzione dei test")
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
            logger.error("Caricamento documento fallito, interruzione dei test")
            return
        
        # Test recupero documenti legacy
        get_docs_result = test_get_legacy_documents(access_token, resources)
        print_test_result(get_docs_result)
        test_results.append(get_docs_result)
        
        # Test accesso negato endpoint admin
        admin_denied_result = test_admin_access_denied(access_token)
        print_test_result(admin_denied_result)
        test_results.append(admin_denied_result)
        
        # Stampa riepilogo
        logger.info("\nRiepilogo Test:")
        logger.info("=" * 50)
        success_count = sum(1 for r in test_results if r.success)
        logger.info(f"Totale Test: {len(test_results)}")
        logger.info(f"Test Riusciti: {success_count}")
        logger.info(f"Test Falliti: {len(test_results) - success_count}")
        logger.info("=" * 50)
        
    finally:
        # Pulizia risorse
        if 'access_token' in locals():
            logger.info("\nPulizia risorse di test...")
            resources.cleanup(access_token)
            logger.info("Pulizia completata")
    
    logger.info("\nTest di Integrazione Completati!")
    logger.info("=" * 50)

if __name__ == "__main__":
    test_register_admin_user()
    # Test di login con le nuove credenziali
    login_result, access_token = test_login()
    if not login_result.success:
        logger.error("Login fallito, interruzione dei test")
        exit(1)
    resources = TestResources()
    test_upload_legacy_document(access_token, resources)
    test_get_legacy_documents(access_token, resources)
    main() 