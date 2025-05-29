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
# TEST_NODE_LOCATION = "Posizione di Test"
TEST_NODE_LOCATION_X = 10.0  # O un altro valore numerico
TEST_NODE_LOCATION_Y = 20.0  # O un altro valore numerico
TEST_NODE_LOCATION_Z = 30.0  # O un altro valore numerico
TEST_NODE_TYPE = "sensor"
TEST_NODE_STATUS = "active"
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
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            headers=get_headers()
        )

        # Includi il log del corpo della risposta per tutti i casi non-successo/non-già-esistente
        if response.status_code not in [200, 400]:
            logger.error(f"Registrazione fallita. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")

        if response.status_code == 200:
            return TestResult(
                "Registrazione",
                True,
                "Utente creato con successo."
            )
        elif response.status_code == 400:
            # Per chiarezza, puoi anche loggare il dettaglio qui se vuoi:
            error_detail = response.json().get("detail", "Dettaglio errore non disponibile.")
            return TestResult(
                "Registrazione",
                True,  # Lo consideriamo un successo perché l'obiettivo del test è proseguire al login
                f"Utente già esistente o errore di validazione: {error_detail}"
            )
        else:
            # Se è un 422 o qualsiasi altro codice di stato inatteso
            return TestResult(
                "Registrazione",
                False,
                f"Codice di stato inatteso: {response.status_code}. Dettaglio: {response.text}"
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
            # Stampa dettagliata per debug
            logger.error(f"Login fallito. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
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
                "location_x": TEST_NODE_LOCATION_X,
                "location_y": TEST_NODE_LOCATION_Y,
                "location_z": TEST_NODE_LOCATION_Z,
                "type": TEST_NODE_TYPE,
                "status": TEST_NODE_STATUS
            },
            headers=get_headers(access_token)
        )

        # Includi il log del corpo della risposta per tutti i casi non-successo
        if response.status_code != 200:
            logger.error(f"Creazione nodo fallita. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            node_id = response_data.get("id")

            # Log dettagliato dei dati ricevuti
            logger.info(f"Dati inviati: name={TEST_NODE_NAME}, house_id={resources.house_id}, location_x={TEST_NODE_LOCATION_X}, location_y={TEST_NODE_LOCATION_Y}, location_z={TEST_NODE_LOCATION_Z}, type={TEST_NODE_TYPE}, status={TEST_NODE_STATUS}")
            logger.info(f"Dati ricevuti: {json.dumps(response_data, indent=2)}")

            # Verifica che l'ID non sia vuoto
            if not node_id:
                return TestResult("Creazione Nodo", False, "ID nodo non presente nella risposta")

            # Verifica che i dati restituiti corrispondano a quelli inviati
            if (response_data.get("name") != TEST_NODE_NAME or
                response_data.get("house_id") != resources.house_id or
                response_data.get("location_x") != TEST_NODE_LOCATION_X or
                response_data.get("location_y") != TEST_NODE_LOCATION_Y or
                response_data.get("location_z") != TEST_NODE_LOCATION_Z or
                response_data.get("type") != TEST_NODE_TYPE or
                response_data.get("status") != TEST_NODE_STATUS):
                return TestResult("Creazione Nodo", False, "Dati nodo non corrispondenti")

            resources.node_id = node_id
            return TestResult("Creazione Nodo", True, f"Nodo creato con ID: {resources.node_id}")
        else:
            # Se è un 422 o qualsiasi altro codice di stato inatteso
            return TestResult(
                "Creazione Nodo",
                False,
                f"Codice di stato inatteso: {response.status_code}. Dettaglio: {response.text}"
            )
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
                logger.error(f"Dati documento legacy ricevuti: {response_data}")
                logger.error(f"Dati attesi: house_id={resources.house_id}, node_id={resources.node_id}, type='TXT', version='1.0', description='Documento di test'")
                return TestResult("Caricamento Documento Legacy", False, "Dati documento non corrispondenti")
            
            resources.document_id = document_id
            return TestResult(
                "Caricamento Documento Legacy",
                True,
                f"Documento caricato con successo con ID: {resources.document_id}"
            )
        else:
            logger.error(f"Caricamento documento fallito. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
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

def admin_login() -> Tuple[TestResult, Optional[str]]:
    """Effettua il login come admin e restituisce il token JWT"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": ADMIN_TEST_EMAIL,
                "password": ADMIN_TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            return TestResult("Login Admin", True, "Token admin ottenuto con successo"), access_token
        else:
            return TestResult("Login Admin", False, f"Codice di stato inatteso: {response.status_code}"), None
    except Exception as e:
        return TestResult("Login Admin", False, str(e)), None

def test_admin_access_allowed(admin_access_token: str) -> TestResult:
    """Test che verifica che un utente admin possa accedere all'endpoint admin-only"""
    try:
        response = requests.get(
            f"{BASE_URL}/users/admin-only",
            headers=get_headers(admin_access_token)
        )
        if response.status_code == 200:
            expected = {"message": "This endpoint is only accessible to admins."}
            if response.json() == expected:
                return TestResult(
                    "Accesso Consentito Endpoint Admin",
                    True,
                    "Accesso admin consentito come previsto con 200 e messaggio corretto"
                )
            else:
                return TestResult(
                    "Accesso Consentito Endpoint Admin",
                    False,
                    f"Messaggio di risposta inatteso: {response.json()}"
                )
        else:
            return TestResult(
                "Accesso Consentito Endpoint Admin",
                False,
                f"Codice di stato inatteso: {response.status_code}"
            )
    except Exception as e:
        return TestResult("Accesso Consentito Endpoint Admin", False, str(e))

def test_read_house_by_id(access_token: str, resources: TestResources) -> TestResult:
    """Test di lettura di una singola casa tramite ID"""
    try:
        if not resources.house_id:
            return TestResult("Lettura Casa", False, "ID casa non disponibile per il test")

        response = requests.get(
            f"{BASE_URL}/houses/{resources.house_id}",
            headers=get_headers(access_token)
        )

        if response.status_code == 200:
            house_data = response.json()
            if house_data.get("id") != resources.house_id:
                return TestResult("Lettura Casa", False, "ID casa non corrispondente")
            return TestResult("Lettura Casa", True, f"Casa recuperata con successo: {house_data}")
        else:
            return TestResult("Lettura Casa", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Lettura Casa", False, str(e))

def test_read_all_houses(access_token: str) -> TestResult:
    """Test di lettura di tutte le case"""
    try:
        response = requests.get(
            f"{BASE_URL}/houses/",
            headers=get_headers(access_token)
        )

        if response.status_code == 200:
            houses = response.json()
            if not isinstance(houses, list):
                return TestResult("Lettura Tutte le Case", False, "Risposta non è una lista")
            return TestResult("Lettura Tutte le Case", True, f"Recuperate {len(houses)} case")
        else:
            return TestResult("Lettura Tutte le Case", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Lettura Tutte le Case", False, str(e))

def test_update_house(access_token: str, resources: TestResources) -> TestResult:
    """Test di aggiornamento di una casa esistente"""
    try:
        if not resources.house_id:
            return TestResult("Aggiornamento Casa", False, "ID casa non disponibile per il test")

        updated_data = {
            "name": "Casa Rinnovata",
            "address": "Via Milano 10, 20100 Milano"
        }

        response = requests.put(
            f"{BASE_URL}/houses/{resources.house_id}",
            json=updated_data,
            headers=get_headers(access_token)
        )

        if response.status_code == 200:
            updated_house = response.json()
            if updated_house.get("name") != updated_data["name"] or updated_house.get("address") != updated_data["address"]:
                return TestResult("Aggiornamento Casa", False, "Dati casa non aggiornati correttamente")
            return TestResult("Aggiornamento Casa", True, f"Casa aggiornata con successo: {updated_house}")
        else:
            return TestResult("Aggiornamento Casa", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Aggiornamento Casa", False, str(e))

def test_delete_house(access_token: str, resources: TestResources) -> TestResult:
    """Test di eliminazione di una casa"""
    try:
        if not resources.house_id:
            return TestResult("Eliminazione Casa", False, "ID casa non disponibile per il test")

        response = requests.delete(
            f"{BASE_URL}/houses/{resources.house_id}",
            headers=get_headers(access_token)
        )

        if response.status_code == 204:
            # Verifica che la casa non esista più
            check_response = requests.get(
                f"{BASE_URL}/houses/{resources.house_id}",
                headers=get_headers(access_token)
            )
            if check_response.status_code == 404:
                resources.house_id = None  # Reset dell'ID dopo l'eliminazione
                return TestResult("Eliminazione Casa", True, "Casa eliminata con successo")
            else:
                return TestResult("Eliminazione Casa", False, "Casa ancora presente dopo l'eliminazione")
        else:
            return TestResult("Eliminazione Casa", False, f"Codice di stato inatteso: {response.status_code}")
    except Exception as e:
        return TestResult("Eliminazione Casa", False, str(e))

def main():
    """Funzione principale di esecuzione dei test"""
    logger.info("Avvio Test di Integrazione...")
    logger.info("=" * 50)
    logger.info("Debug: Inizio esecuzione dei test di integrazione")
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
        
        # Login admin e test accesso consentito endpoint admin
        admin_login_result, admin_access_token = admin_login()
        print_test_result(admin_login_result)
        test_results.append(admin_login_result)
        if admin_access_token:
            admin_allowed_result = test_admin_access_allowed(admin_access_token)
            print_test_result(admin_allowed_result)
            test_results.append(admin_allowed_result)
        else:
            logger.error("Token admin non ottenuto, test accesso consentito endpoint admin saltato")
        
        # Test CRUD per House
        read_result = test_read_house_by_id(access_token, resources)
        print_test_result(read_result)
        test_results.append(read_result)

        read_all_result = test_read_all_houses(access_token)
        print_test_result(read_all_result)
        test_results.append(read_all_result)

        update_result = test_update_house(access_token, resources)
        print_test_result(update_result)
        test_results.append(update_result)

        delete_result = test_delete_house(access_token, resources)
        print_test_result(delete_result)
        test_results.append(delete_result)
        
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
    main() 